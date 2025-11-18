"""
Servicio para interactuar con Qdrant como base de datos vectorial.
Proporciona operaciones CRUD y búsqueda semántica.
"""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)
from qdrant_client.http.exceptions import UnexpectedResponse
from app.config.settings import settings
from app.core.logging import get_logger
from app.core.exceptions import QdrantConnectionError, QdrantOperationError

logger = get_logger(__name__)


class QdrantService:
    """
    Servicio para gestionar operaciones con Qdrant.
    Maneja conexión, colección y operaciones CRUD sobre vectores.
    """
    
    def __init__(
        self, 
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        """
        Inicializa el cliente de Qdrant.
        
        Args:
            url: URL de conexión a Qdrant (default: desde settings)
            api_key: API Key para autenticación (default: desde settings)
            collection_name: Nombre de la colección (default: desde settings)
        """
        self.url = url or settings.qdrant_url
        self.api_key = api_key or settings.qdrant_api_key
        self.collection_name = collection_name or settings.qdrant_collection_name
        
        # Inicializar cliente
        try:
            if self.api_key:
                self.client = QdrantClient(
                    url=self.url,
                    api_key=self.api_key
                )
                logger.info(
                    "Cliente Qdrant inicializado con autenticación",
                    url=self.url,
                    collection=self.collection_name
                )
            else:
                self.client = QdrantClient(url=self.url)
                logger.info(
                    "Cliente Qdrant inicializado sin autenticación",
                    url=self.url,
                    collection=self.collection_name
                )
        except Exception as e:
            logger.error(
                "Error inicializando cliente Qdrant",
                error=str(e),
                url=self.url
            )
            raise QdrantConnectionError(
                message=f"No se pudo conectar a Qdrant: {str(e)}",
                url=self.url
            )
    
    def ensure_collection(self, vector_size: int = 1536) -> None:
        """
        Crea la colección si no existe.
        
        Args:
            vector_size: Dimensión de los vectores (default: 1536 para OpenAI)
            
        Raises:
            Exception: Si falla la creación de la colección
        """
        try:
            # Verificar si la colección existe
            collections = self.client.get_collections().collections
            collection_exists = any(
                col.name == self.collection_name for col in collections
            )
            
            if collection_exists:
                logger.info(
                    "Colección ya existe",
                    collection=self.collection_name
                )
                return
            
            # Crear colección con configuración
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            
            logger.info(
                "Colección creada exitosamente",
                collection=self.collection_name,
                vector_size=vector_size,
                distance="COSINE"
            )
            
        except Exception as e:
            logger.error(
                "Error creando colección",
                collection=self.collection_name,
                error=str(e),
                error_type=type(e).__name__
            )
            raise QdrantOperationError(
                operation="create_collection",
                details_msg=str(e),
                collection=self.collection_name
            )
    
    def upsert_point(
        self, 
        point_id: int, 
        vector: List[float], 
        payload: Dict[str, Any]
    ) -> None:
        """
        Inserta o actualiza un punto en Qdrant.
        
        Args:
            point_id: ID único del punto
            vector: Vector de embeddings
            payload: Metadatos asociados al punto
            
        Raises:
            Exception: Si falla la operación de upsert
        """
        try:
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(
                "Punto insertado/actualizado exitosamente",
                collection=self.collection_name,
                point_id=point_id,
                payload_keys=list(payload.keys())
            )
            
        except Exception as e:
            logger.error(
                "Error en upsert de punto",
                collection=self.collection_name,
                point_id=point_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise QdrantOperationError(
                operation="upsert_point",
                details_msg=str(e),
                collection=self.collection_name
            )
    
    def delete_point(self, point_id: int) -> bool:
        """
        Elimina un punto de Qdrant.
        
        Args:
            point_id: ID del punto a eliminar
            
        Returns:
            bool: True si se eliminó, False si no existía
            
        Raises:
            Exception: Si falla la operación de eliminación
        """
        try:
            # Verificar si el punto existe antes de eliminar
            try:
                result = self.client.retrieve(
                    collection_name=self.collection_name,
                    ids=[point_id]
                )
                
                if not result:
                    logger.warning(
                        "Punto no encontrado para eliminar",
                        collection=self.collection_name,
                        point_id=point_id
                    )
                    return False
            except Exception:
                # Si falla la verificación, asumir que no existe
                return False
            
            # Eliminar el punto
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[point_id]
            )
            
            logger.info(
                "Punto eliminado exitosamente",
                collection=self.collection_name,
                point_id=point_id
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Error eliminando punto",
                collection=self.collection_name,
                point_id=point_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise QdrantOperationError(
                operation="delete_point",
                details_msg=str(e),
                collection=self.collection_name
            )
    
    def search_similar(
        self, 
        query_vector: List[float], 
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca puntos similares al vector de consulta.
        
        Args:
            query_vector: Vector de la consulta
            limit: Número máximo de resultados
            score_threshold: Umbral mínimo de similitud (opcional)
            
        Returns:
            List[Dict]: Lista de resultados con payload y score
            
        Raises:
            Exception: Si falla la búsqueda
        """
        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Convertir resultados a formato dict
            results = []
            for scored_point in search_result:
                result = {
                    "id": scored_point.id,
                    "score": scored_point.score,
                    "payload": scored_point.payload
                }
                results.append(result)
            
            logger.info(
                "Búsqueda completada",
                collection=self.collection_name,
                results_found=len(results),
                limit=limit
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Error en búsqueda",
                collection=self.collection_name,
                error=str(e),
                error_type=type(e).__name__
            )
            raise QdrantOperationError(
                operation="search_similar",
                details_msg=str(e),
                collection=self.collection_name
            )
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica el estado de la conexión con Qdrant.
        
        Returns:
            Dict: Estado de salud del servicio
        """
        try:
            # Intentar obtener información de colecciones
            collections = self.client.get_collections()
            
            # Verificar si nuestra colección existe
            collection_exists = any(
                col.name == self.collection_name 
                for col in collections.collections
            )
            
            # Si la colección existe, obtener información adicional
            collection_info = None
            if collection_exists:
                try:
                    info = self.client.get_collection(self.collection_name)
                    collection_info = {
                        "vectors_count": info.vectors_count,
                        "points_count": info.points_count,
                        "status": info.status
                    }
                except Exception as e:
                    logger.warning(f"No se pudo obtener info de colección: {e}")
            
            return {
                "status": "healthy",
                "url": self.url,
                "collection_name": self.collection_name,
                "collection_exists": collection_exists,
                "collection_info": collection_info,
                "total_collections": len(collections.collections)
            }
            
        except Exception as e:
            logger.error(
                "Health check falló",
                error=str(e),
                error_type=type(e).__name__
            )
            return {
                "status": "unhealthy",
                "url": self.url,
                "collection_name": self.collection_name,
                "error": str(e)
            }
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Obtiene información detallada de la colección.
        
        Returns:
            Dict: Información de la colección
        """
        try:
            info = self.client.get_collection(self.collection_name)
            
            return {
                "collection_name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
                "vector_size": info.config.params.vectors.size,
                "distance": info.config.params.vectors.distance.name
            }
            
        except Exception as e:
            logger.warning(
                "No se pudo obtener información de colección",
                collection=self.collection_name,
                error=str(e)
            )
            return {
                "collection_name": self.collection_name,
                "error": str(e)
            }


# Instancia global del servicio
_qdrant_service: Optional[QdrantService] = None


def get_qdrant_service() -> QdrantService:
    """
    Obtiene la instancia global del servicio de Qdrant.
    Implementa patrón singleton para reutilizar la conexión.
    
    Returns:
        QdrantService: Instancia del servicio
    """
    global _qdrant_service
    
    if _qdrant_service is None:
        _qdrant_service = QdrantService()
        logger.info("Instancia global de QdrantService creada")
    
    return _qdrant_service


def reset_qdrant_service() -> None:
    """
    Resetea la instancia global del servicio.
    Útil para testing o reconfiguración.
    """
    global _qdrant_service
    _qdrant_service = None
    logger.info("Instancia global de QdrantService reseteada")
