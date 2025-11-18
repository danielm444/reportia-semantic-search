"""
Servicio de búsqueda y sincronización con Qdrant.
Proporciona operaciones de búsqueda semántica y sincronización con BD relacional.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from app.config.settings import settings
from app.core.logging import get_logger
from app.core.exceptions import SearchError, QueryNotFoundError
from app.services.embedding_service import EmbeddingService, get_embedding_service
from app.services.qdrant_service import QdrantService, get_qdrant_service
from app.core.text_normalizer import normalize_query

logger = get_logger(__name__)


class SearchService:
    """
    Servicio de búsqueda y sincronización con Qdrant.
    Maneja búsquedas semánticas y operaciones de sincronización (upsert, delete).
    """
    
    def __init__(
        self, 
        embedding_service: Optional[EmbeddingService] = None,
        qdrant_service: Optional[QdrantService] = None
    ):
        """
        Inicializa el servicio de búsqueda.
        
        Args:
            embedding_service: Servicio de embeddings personalizado (opcional)
            qdrant_service: Servicio de Qdrant personalizado (opcional)
        """
        self.embedding_service = embedding_service or get_embedding_service()
        self.qdrant_service = qdrant_service or get_qdrant_service()
        
        # Asegurar que la colección existe
        try:
            self.qdrant_service.ensure_collection(vector_size=1536)
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
    
    async def upsert_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea o actualiza una consulta en Qdrant.
        
        Args:
            query_data: Diccionario con datos de saved_query
            
        Returns:
            Dict con id y status
            
        Raises:
            SearchError: Si falla la operación
        """
        try:
            query_id = query_data.get("id")
            if not query_id:
                raise ValueError("El campo 'id' es requerido")
            
            # Combinar name y description para generar texto indexable
            name = query_data.get("name", "")
            description = query_data.get("description", "") or ""
            
            indexable_text = f"{name} {description}".strip()
            
            if not indexable_text:
                raise ValueError("Se requiere al menos 'name' o 'description'")
            
            logger.info(
                "Iniciando upsert de consulta",
                query_id=query_id,
                name=name[:50],
                indexable_text_length=len(indexable_text)
            )
            
            # Generar embedding
            embedding = await self.embedding_service.embed_query(indexable_text)
            
            # Preparar payload con todos los metadatos
            payload = {
                "id": query_id,
                "name": name,
                "description": description,
                "query_sql_original": query_data.get("query_sql_original", ""),
                "query_sql_param": query_data.get("query_sql_param"),
                "parameters_json": query_data.get("parameters_json"),
                "engine_code": query_data.get("engine_code", ""),
                "company_id": query_data.get("company_id"),
                "owner_user_id": query_data.get("owner_user_id"),
                "version": query_data.get("version", 1),
                "is_active": query_data.get("is_active", True),
                "created_at": query_data.get("created_at"),
                "updated_at": query_data.get("updated_at")
            }
            
            # Convertir datetime a string si es necesario
            if isinstance(payload["created_at"], datetime):
                payload["created_at"] = payload["created_at"].isoformat()
            if isinstance(payload["updated_at"], datetime):
                payload["updated_at"] = payload["updated_at"].isoformat()
            
            # Upsert en Qdrant
            self.qdrant_service.upsert_point(
                point_id=query_id,
                vector=embedding,
                payload=payload
            )
            
            logger.info(
                "Upsert completado exitosamente",
                query_id=query_id,
                name=name[:50]
            )
            
            return {
                "id": query_id,
                "status": "success",
                "message": "Consulta sincronizada exitosamente"
            }
            
        except ValueError as e:
            logger.warning(f"Parámetros inválidos para upsert: {e}")
            raise SearchError(
                f"Parámetros inválidos: {str(e)}",
                query=str(query_data.get("id"))
            )
        except Exception as e:
            logger.error(
                "Error en upsert de consulta",
                error=str(e),
                error_type=type(e).__name__,
                query_id=query_data.get("id")
            )
            raise SearchError(
                "Error sincronizando consulta",
                query=str(query_data.get("id"))
            )
    
    async def delete_query(self, query_id: int) -> bool:
        """
        Elimina una consulta de Qdrant.
        
        Args:
            query_id: ID de la consulta
            
        Returns:
            True si se eliminó, False si no existía
            
        Raises:
            QueryNotFoundError: Si la consulta no existe
            SearchError: Si falla la operación
        """
        try:
            logger.info(
                "Iniciando eliminación de consulta",
                query_id=query_id
            )
            
            # Intentar eliminar
            deleted = self.qdrant_service.delete_point(query_id)
            
            if not deleted:
                logger.warning(
                    "Consulta no encontrada para eliminar",
                    query_id=query_id
                )
                raise QueryNotFoundError(query_id)
            
            logger.info(
                "Consulta eliminada exitosamente",
                query_id=query_id
            )
            
            return True
            
        except QueryNotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Error eliminando consulta",
                error=str(e),
                error_type=type(e).__name__,
                query_id=query_id
            )
            raise SearchError(
                "Error eliminando consulta",
                query=str(query_id)
            )
    
    async def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Realiza búsqueda semántica de consultas guardadas.
        
        Args:
            query: Texto de búsqueda en lenguaje natural
            top_k: Número de resultados a retornar
            
        Returns:
            List[Dict[str, Any]]: Lista de resultados con metadatos y scores
            
        Raises:
            SearchError: Si falla la búsqueda
        """
        try:
            if not query or not query.strip():
                raise ValueError("La consulta no puede estar vacía")
            
            if top_k <= 0:
                raise ValueError("top_k debe ser mayor que 0")
            
            # Normalizar consulta
            normalized_query = normalize_query(query)
            
            # Iniciar medición de tiempo
            import time
            start_time = time.time()
            
            logger.info(
                "Búsqueda semántica iniciada",
                query_length=len(query),
                original_query=query[:100] + "..." if len(query) > 100 else query,
                normalized_query=normalized_query[:100] + "..." if len(normalized_query) > 100 else normalized_query,
                top_k=top_k
            )
            
            # Generar embedding de la consulta
            query_embedding = await self.embedding_service.embed_query(normalized_query)
            
            # Buscar en Qdrant
            search_results = self.qdrant_service.search_similar(
                query_vector=query_embedding,
                limit=top_k
            )
            
            # Construir resultados con formato esperado
            results = []
            for result in search_results:
                payload = result["payload"]
                score = result["score"]
                
                # Crear resultado con todos los metadatos
                query_result = {
                    "data": {
                        "id": payload.get("id"),
                        "name": payload.get("name"),
                        "description": payload.get("description"),
                        "query_sql_original": payload.get("query_sql_original"),
                        "query_sql_param": payload.get("query_sql_param"),
                        "parameters_json": payload.get("parameters_json"),
                        "engine_code": payload.get("engine_code"),
                        "company_id": payload.get("company_id"),
                        "owner_user_id": payload.get("owner_user_id"),
                        "version": payload.get("version"),
                        "is_active": payload.get("is_active"),
                        "created_at": payload.get("created_at"),
                        "updated_at": payload.get("updated_at")
                    },
                    "score": round(score, 4)
                }
                results.append(query_result)
            
            # Calcular tiempo de respuesta
            end_time = time.time()
            response_time = end_time - start_time
            
            # Validar tiempo de respuesta (requisito < 2 segundos)
            if response_time >= 2.0:
                logger.warning(
                    "Tiempo de respuesta excede límite",
                    response_time=response_time,
                    limit_seconds=2.0,
                    query_length=len(query)
                )
            
            logger.info(
                "Búsqueda completada exitosamente",
                results_found=len(results),
                query_length=len(query),
                top_k=top_k,
                response_time_seconds=round(response_time, 3),
                scores_range=f"{min(r['score'] for r in results):.3f}-{max(r['score'] for r in results):.3f}" if results else "N/A"
            )
            
            return results
            
        except ValueError as e:
            logger.warning(f"Parámetros inválidos para búsqueda: {e}")
            raise SearchError(
                f"Parámetros inválidos: {str(e)}",
                query=query
            )
        except Exception as e:
            logger.error(
                "Error durante búsqueda semántica",
                error=str(e),
                error_type=type(e).__name__,
                query_length=len(query) if query else 0,
                top_k=top_k
            )
            raise SearchError(
                "Error durante la búsqueda semántica",
                query=query
            )
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre la colección de Qdrant.
        
        Returns:
            Dict[str, Any]: Información de la colección
        """
        return self.qdrant_service.get_collection_info()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica el estado del servicio de búsqueda.
        
        Returns:
            Dict[str, Any]: Estado del servicio
        """
        try:
            # Health check de Qdrant
            qdrant_health = self.qdrant_service.health_check()
            
            # Health check de embeddings
            embedding_health = self.embedding_service.health_check()
            
            # Determinar estado general
            overall_status = "healthy"
            if (qdrant_health.get("status") != "healthy" or 
                embedding_health.get("status") != "healthy"):
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "qdrant": qdrant_health,
                "embedding_service": embedding_health
            }
            
        except Exception as e:
            logger.error(f"Health check de búsqueda falló: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Instancia global del servicio
_search_service: Optional[SearchService] = None


def get_search_service() -> SearchService:
    """
    Obtiene la instancia global del servicio de búsqueda.
    Implementa patrón singleton para reutilizar la conexión.
    
    Returns:
        SearchService: Instancia del servicio
    """
    global _search_service
    
    if _search_service is None:
        _search_service = SearchService()
        logger.info("Instancia global de SearchService creada")
    
    return _search_service


def reset_search_service() -> None:
    """
    Resetea la instancia global del servicio.
    Útil para testing o reconfiguración.
    """
    global _search_service
    _search_service = None
    logger.info("Instancia global de SearchService reseteada")
