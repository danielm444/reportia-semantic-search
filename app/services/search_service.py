"""
Servicio de búsqueda y sincronización con Qdrant.

Expone un núcleo **genérico** de documentos (id + texto + payload libre) sobre
el que se construyen adaptadores de dominio (p. ej. consultas SQL guardadas).
El payload se devuelve íntegro en las búsquedas, por lo que el servicio sirve
para indexar cualquier tipo de contenido (items de menú, saved queries, etc.).
"""

import time
import uuid
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from app.config.settings import settings
from app.core.logging import get_logger
from app.core.exceptions import SearchError, QueryNotFoundError
from app.services.embedding_service import EmbeddingService, get_embedding_service
from app.services.qdrant_service import QdrantService, get_qdrant_service
from app.core.text_normalizer import normalize_query

logger = get_logger(__name__)

# Namespace estable para derivar point-ids UUID a partir de ids string
_ID_NAMESPACE = uuid.UUID("a3f1c2d4-5b6e-7a8b-9c0d-1e2f3a4b5c6d")

DocumentId = Union[int, str]


def coerce_point_id(doc_id: DocumentId) -> Union[int, str]:
    """
    Convierte un id de documento en un point-id válido para Qdrant.

    Qdrant solo acepta enteros sin signo o UUIDs. Por eso:
    - ``int`` se usa tal cual.
    - ``str`` con forma de UUID se usa tal cual.
    - cualquier otro ``str`` se mapea de forma determinista a un UUID v5,
      conservando el id original dentro del payload.

    Args:
        doc_id: Identificador del documento (int o str)

    Returns:
        int | str: Point-id apto para Qdrant
    """
    if isinstance(doc_id, int):
        return doc_id
    if isinstance(doc_id, str):
        try:
            return str(uuid.UUID(doc_id))
        except ValueError:
            return str(uuid.uuid5(_ID_NAMESPACE, doc_id))
    raise ValueError(f"id de documento no soportado: {type(doc_id).__name__}")


class SearchService:
    """
    Servicio de búsqueda y sincronización con Qdrant.

    Núcleo genérico (``upsert_document``/``upsert_documents``/``delete_document``/
    ``search``) más adaptadores de compatibilidad para saved queries
    (``upsert_query``/``delete_query``).
    """

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        qdrant_service: Optional[QdrantService] = None,
        vector_size: int = 1536
    ):
        """
        Inicializa el servicio de búsqueda.

        Args:
            embedding_service: Servicio de embeddings personalizado (opcional)
            qdrant_service: Servicio de Qdrant personalizado (opcional)
            vector_size: Dimensión de los vectores de la colección
        """
        self.embedding_service = embedding_service or get_embedding_service()
        self.qdrant_service = qdrant_service or get_qdrant_service()
        self.vector_size = vector_size

        # Asegurar que la colección existe
        try:
            self.qdrant_service.ensure_collection(vector_size=vector_size)
        except Exception as e:
            logger.warning(
                "No se pudo crear colección durante inicialización",
                error=str(e)
            )

        logger.info(
            "Servicio de búsqueda inicializado",
            qdrant_url=self.qdrant_service.url,
            collection=self.qdrant_service.collection_name,
            embedding_service_type=type(self.embedding_service).__name__
        )

    # ------------------------------------------------------------------ #
    # Núcleo genérico
    # ------------------------------------------------------------------ #

    async def upsert_document(
        self,
        doc_id: DocumentId,
        text: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Crea o actualiza un documento genérico en Qdrant.

        Args:
            doc_id: Identificador del documento (int o str)
            text: Texto a vectorizar
            payload: Metadatos arbitrarios a almacenar y devolver en búsquedas

        Returns:
            Dict con ``id`` y ``status``

        Raises:
            SearchError: Si los parámetros son inválidos o falla la operación
        """
        result = await self.upsert_documents([
            {"id": doc_id, "texto": text, "payload": payload or {}}
        ])
        return {
            "id": doc_id,
            "status": "success",
            "message": "Documento sincronizado exitosamente",
            "count": result["count"],
        }

    async def upsert_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Crea o actualiza múltiples documentos genéricos en un solo lote.

        Cada documento es un dict ``{"id", "texto", "payload"}``. Genera los
        embeddings en una sola llamada y hace upsert en lote en Qdrant.

        Args:
            documents: Lista de documentos a indexar

        Returns:
            Dict con ``count`` (cantidad indexada) e ``ids``

        Raises:
            SearchError: Si los parámetros son inválidos o falla la operación
        """
        try:
            if not documents:
                raise ValueError("La lista de documentos no puede estar vacía")

            prepared = []
            for doc in documents:
                doc_id = doc.get("id")
                text = (doc.get("texto") or doc.get("text") or "").strip()
                payload = dict(doc.get("payload") or {})

                if doc_id is None:
                    raise ValueError("Cada documento requiere un 'id'")
                if not text:
                    raise ValueError(f"El documento '{doc_id}' requiere 'texto' no vacío")

                # Conservar el id original dentro del payload para que viaje
                # en los resultados de búsqueda.
                payload.setdefault("id", doc_id)
                prepared.append({
                    "point_id": coerce_point_id(doc_id),
                    "text": text,
                    "payload": payload,
                })

            logger.info("Iniciando upsert de documentos", count=len(prepared))

            # Embeddings en lote (una sola llamada al proveedor)
            embeddings = await self.embedding_service.embed_documents(
                [p["text"] for p in prepared]
            )

            if len(embeddings) != len(prepared):
                raise SearchError(
                    f"Discrepancia en embeddings: {len(embeddings)} vs {len(prepared)}"
                )

            points = [
                {"id": p["point_id"], "vector": embeddings[i], "payload": p["payload"]}
                for i, p in enumerate(prepared)
            ]
            self.qdrant_service.upsert_points(points)

            ids = [doc.get("id") for doc in documents]
            logger.info("Upsert de documentos completado", count=len(points))
            return {"count": len(points), "ids": ids}

        except ValueError as e:
            logger.warning(f"Parámetros inválidos para upsert de documentos: {e}")
            raise SearchError(f"Parámetros inválidos: {str(e)}")
        except SearchError:
            raise
        except Exception as e:
            logger.error(
                "Error en upsert de documentos",
                error=str(e),
                error_type=type(e).__name__
            )
            raise SearchError("Error sincronizando documentos")

    def delete_document(self, doc_id: DocumentId) -> bool:
        """
        Elimina un documento de Qdrant.

        Args:
            doc_id: Identificador del documento

        Returns:
            True si se eliminó, False si no existía

        Raises:
            SearchError: Si falla la operación
        """
        try:
            point_id = coerce_point_id(doc_id)
            logger.info("Iniciando eliminación de documento", doc_id=doc_id)
            return self.qdrant_service.delete_point(point_id)
        except Exception as e:
            logger.error(
                "Error eliminando documento",
                error=str(e),
                error_type=type(e).__name__,
                doc_id=doc_id
            )
            raise SearchError("Error eliminando documento")

    async def search(
        self,
        query: str,
        top_k: int = 10,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Realiza búsqueda semántica genérica.

        Args:
            query: Texto de búsqueda en lenguaje natural
            top_k: Número de resultados a retornar
            score_threshold: Umbral mínimo de similitud (opcional)
            filters: Filtros de igualdad sobre el payload (opcional)
            offset: Resultados a saltar (paginación)

        Returns:
            List[Dict]: ``[{"id", "score", "data": <payload completo>}]``

        Raises:
            SearchError: Si falla la búsqueda
        """
        try:
            if not query or not query.strip():
                raise ValueError("La consulta no puede estar vacía")
            if top_k <= 0:
                raise ValueError("top_k debe ser mayor que 0")
            if offset < 0:
                raise ValueError("offset no puede ser negativo")

            normalized_query = normalize_query(query)
            start_time = time.time()

            logger.info(
                "Búsqueda semántica iniciada",
                query_length=len(query),
                top_k=top_k,
                offset=offset,
                has_filters=bool(filters),
                score_threshold=score_threshold,
            )

            query_embedding = await self.embedding_service.embed_query(normalized_query)
            query_filter = self.qdrant_service.build_filter(filters)

            search_results = self.qdrant_service.search_similar(
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=query_filter,
                offset=offset,
            )

            results = [
                {
                    "id": result.get("id"),
                    "score": round(result["score"], 4),
                    "data": result.get("payload") or {},
                }
                for result in search_results
            ]

            response_time = time.time() - start_time
            if response_time >= 2.0:
                logger.warning(
                    "Tiempo de respuesta excede límite",
                    response_time=response_time,
                    limit_seconds=2.0,
                )

            logger.info(
                "Búsqueda completada exitosamente",
                results_found=len(results),
                top_k=top_k,
                response_time_seconds=round(response_time, 3),
                scores_range=(
                    f"{min(r['score'] for r in results):.3f}-"
                    f"{max(r['score'] for r in results):.3f}"
                    if results else "N/A"
                ),
            )

            return results

        except ValueError as e:
            logger.warning(f"Parámetros inválidos para búsqueda: {e}")
            raise SearchError(f"Parámetros inválidos: {str(e)}", query=query)
        except SearchError:
            raise
        except Exception as e:
            logger.error(
                "Error durante búsqueda semántica",
                error=str(e),
                error_type=type(e).__name__,
                top_k=top_k,
            )
            raise SearchError("Error durante la búsqueda semántica", query=query)

    # ------------------------------------------------------------------ #
    # Adaptadores de compatibilidad: saved queries
    # ------------------------------------------------------------------ #

    @staticmethod
    def _saved_query_to_document(query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traduce un dict de saved_query a un documento genérico."""
        query_id = query_data.get("id")
        if not query_id:
            raise ValueError("El campo 'id' es requerido")

        name = query_data.get("name", "")
        description = query_data.get("description", "") or ""
        indexable_text = f"{name} {description}".strip()
        if not indexable_text:
            raise ValueError("Se requiere al menos 'name' o 'description'")

        payload = dict(query_data)
        # Normalizar datetimes a ISO 8601 para que Qdrant los acepte
        for field in ("created_at", "updated_at"):
            if isinstance(payload.get(field), datetime):
                payload[field] = payload[field].isoformat()

        return {"id": query_id, "texto": indexable_text, "payload": payload}

    async def upsert_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea o actualiza una consulta guardada (adaptador sobre el núcleo genérico).

        Args:
            query_data: Diccionario con datos de saved_query

        Returns:
            Dict con id y status
        """
        try:
            document = self._saved_query_to_document(query_data)
        except ValueError as e:
            logger.warning(f"Parámetros inválidos para upsert: {e}")
            raise SearchError(
                f"Parámetros inválidos: {str(e)}",
                query=str(query_data.get("id")),
            )

        await self.upsert_documents([document])
        return {
            "id": document["id"],
            "status": "success",
            "message": "Consulta sincronizada exitosamente",
        }

    async def upsert_queries(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upsert en lote de saved queries (adaptador)."""
        documents = [self._saved_query_to_document(q) for q in queries]
        result = await self.upsert_documents(documents)
        return {"count": result["count"], "ids": result["ids"]}

    async def delete_query(self, query_id: int) -> bool:
        """
        Elimina una consulta guardada.

        Args:
            query_id: ID de la consulta

        Returns:
            True si se eliminó

        Raises:
            QueryNotFoundError: Si la consulta no existe
            SearchError: Si falla la operación
        """
        try:
            deleted = self.delete_document(query_id)
            if not deleted:
                logger.warning("Consulta no encontrada para eliminar", query_id=query_id)
                raise QueryNotFoundError(query_id)
            logger.info("Consulta eliminada exitosamente", query_id=query_id)
            return True
        except QueryNotFoundError:
            raise
        except SearchError:
            raise
        except Exception as e:
            logger.error(
                "Error eliminando consulta",
                error=str(e),
                error_type=type(e).__name__,
                query_id=query_id,
            )
            raise SearchError("Error eliminando consulta", query=str(query_id))

    # ------------------------------------------------------------------ #
    # Diagnóstico
    # ------------------------------------------------------------------ #

    def get_collection_info(self) -> Dict[str, Any]:
        """Obtiene información sobre la colección de Qdrant."""
        return self.qdrant_service.get_collection_info()

    def health_check(self) -> Dict[str, Any]:
        """Verifica el estado del servicio de búsqueda y sus dependencias."""
        try:
            qdrant_health = self.qdrant_service.health_check()
            embedding_health = self.embedding_service.health_check()

            overall_status = "healthy"
            if (qdrant_health.get("status") != "healthy" or
                    embedding_health.get("status") != "healthy"):
                overall_status = "degraded"

            return {
                "status": overall_status,
                "qdrant": qdrant_health,
                "embedding_service": embedding_health,
            }
        except Exception as e:
            logger.error(f"Health check de búsqueda falló: {e}")
            return {"status": "unhealthy", "error": str(e)}


# Instancia global del servicio
_search_service: Optional[SearchService] = None


def get_search_service() -> SearchService:
    """
    Obtiene la instancia global del servicio de búsqueda (singleton).

    Returns:
        SearchService: Instancia del servicio
    """
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
        logger.info("Instancia global de SearchService creada")
    return _search_service


def reset_search_service() -> None:
    """Resetea la instancia global del servicio (útil para testing)."""
    global _search_service
    _search_service = None
    logger.info("Instancia global de SearchService reseteada")
