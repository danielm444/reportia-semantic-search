"""
Servicio de embeddings usando LangChain como capa de abstracción.
Permite cambiar fácilmente entre diferentes proveedores de embeddings.
"""

import time
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings
from app.config.settings import settings
from app.core.logging import get_logger
from app.core.exceptions import EmbeddingServiceError, ConfigurationError

logger = get_logger(__name__)


class EmbeddingService:
    """
    Servicio de embeddings que usa LangChain como abstracción.
    Permite cambiar proveedores modificando solo la inicialización.
    """
    
    def __init__(self, embeddings_provider: Optional[Embeddings] = None):
        """
        Inicializa el servicio de embeddings.
        
        Args:
            embeddings_provider: Proveedor de embeddings personalizado (opcional)
        """
        self.embeddings = embeddings_provider or self._create_default_embeddings()
        logger.info(
            "Servicio de embeddings inicializado",
            provider=type(self.embeddings).__name__
        )
    
    def _create_default_embeddings(self) -> Embeddings:
        """
        Crea el proveedor de embeddings por defecto (OpenAI).
        
        Returns:
            Embeddings: Instancia del proveedor de embeddings
            
        Raises:
            ConfigurationError: Si la configuración es inválida
        """
        try:
            # Validar configuración
            if not settings.openai_api_key:
                raise ConfigurationError(
                    "OPENAI_API_KEY no configurada",
                    details={"required_env": "OPENAI_API_KEY"}
                )
            
            # Crear instancia de OpenAI Embeddings con configuración optimizada
            # Usar valores por defecto si los nuevos campos no están disponibles
            max_retries = getattr(settings, 'openai_max_retries', 2)
            timeout = getattr(settings, 'openai_timeout', 10.0)
            max_concurrent = getattr(settings, 'openai_max_concurrent', 5)
            
            embeddings = OpenAIEmbeddings(
                api_key=settings.openai_api_key,
                model="text-embedding-3-small",
                # Configuraciones optimizadas para rendimiento
                max_retries=max_retries,
                request_timeout=timeout,
                show_progress_bar=False,
                # Configuraciones adicionales para optimización
                chunk_size=1000,  # Procesar en chunks más grandes
                # Headers para optimizar conexión
                default_headers={
                    "Connection": "keep-alive",
                    "Keep-Alive": "timeout=30, max=100"
                }
            )
            
            logger.info(
                "Proveedor de embeddings OpenAI configurado (optimizado)",
                model="text-embedding-3-small",
                max_retries=max_retries,
                timeout=timeout,
                chunk_size=1000
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(
                "Error configurando proveedor de embeddings",
                error=str(e),
                provider="OpenAI"
            )
            raise ConfigurationError(
                f"Error configurando OpenAI Embeddings: {str(e)}",
                details={"provider": "OpenAI", "error": str(e)}
            )
    
    async def embed_query(self, text: str) -> List[float]:
        """
        Genera embedding para una consulta de texto.
        
        Args:
            text: Texto a convertir en embedding
            
        Returns:
            List[float]: Vector de embedding
            
        Raises:
            EmbeddingServiceError: Si falla la generación del embedding
        """
        try:
            if not text or not text.strip():
                raise ValueError("El texto no puede estar vacío")
            
            logger.debug(
                "Generando embedding para consulta",
                text_length=len(text),
                text_preview=text[:50] + "..." if len(text) > 50 else text
            )
            
            # Usar LangChain para generar embedding
            embedding = await self.embeddings.aembed_query(text.strip())
            
            logger.debug(
                "Embedding generado exitosamente",
                embedding_dimension=len(embedding),
                text_length=len(text)
            )
            
            return embedding
            
        except ValueError as e:
            logger.warning(f"Entrada inválida para embedding: {e}")
            raise EmbeddingServiceError(
                f"Entrada inválida: {str(e)}",
                original_error=str(e)
            )
        except Exception as e:
            logger.error(
                "Error generando embedding",
                error=str(e),
                error_type=type(e).__name__,
                text_length=len(text) if text else 0
            )
            raise EmbeddingServiceError(
                "Error generando embedding para consulta",
                original_error=str(e)
            )
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Genera embeddings para múltiples documentos.
        
        Args:
            texts: Lista de textos a convertir en embeddings
            
        Returns:
            List[List[float]]: Lista de vectores de embedding
            
        Raises:
            EmbeddingServiceError: Si falla la generación de embeddings
        """
        try:
            if not texts:
                raise ValueError("La lista de textos no puede estar vacía")
            
            # Filtrar textos vacíos
            valid_texts = [text.strip() for text in texts if text and text.strip()]
            if not valid_texts:
                raise ValueError("No hay textos válidos para procesar")
            
            logger.info(
                "Generando embeddings para documentos",
                total_documents=len(valid_texts),
                avg_length=sum(len(text) for text in valid_texts) // len(valid_texts)
            )
            
            # Usar LangChain para generar embeddings en lote
            embeddings = await self.embeddings.aembed_documents(valid_texts)
            
            logger.info(
                "Embeddings generados exitosamente",
                documents_processed=len(embeddings),
                embedding_dimension=len(embeddings[0]) if embeddings else 0
            )
            
            return embeddings
            
        except ValueError as e:
            logger.warning(f"Entrada inválida para embeddings: {e}")
            raise EmbeddingServiceError(
                f"Entrada inválida: {str(e)}",
                original_error=str(e)
            )
        except Exception as e:
            logger.error(
                "Error generando embeddings para documentos",
                error=str(e),
                error_type=type(e).__name__,
                document_count=len(texts) if texts else 0
            )
            raise EmbeddingServiceError(
                "Error generando embeddings para documentos",
                original_error=str(e)
            )
    
    def embed_query_sync(self, text: str) -> List[float]:
        """
        Versión síncrona de embed_query para compatibilidad.
        
        Args:
            text: Texto a convertir en embedding
            
        Returns:
            List[float]: Vector de embedding
            
        Raises:
            EmbeddingServiceError: Si falla la generación del embedding
        """
        try:
            if not text or not text.strip():
                raise ValueError("El texto no puede estar vacío")
            
            logger.debug(
                "Generando embedding síncrono para consulta",
                text_length=len(text),
                text_preview=text[:50] + "..." if len(text) > 50 else text
            )
            
            # Usar método síncrono de LangChain
            embedding = self.embeddings.embed_query(text.strip())
            
            logger.debug(
                "Embedding síncrono generado exitosamente",
                embedding_dimension=len(embedding),
                text_length=len(text)
            )
            
            return embedding
            
        except ValueError as e:
            logger.warning(f"Entrada inválida para embedding síncrono: {e}")
            raise EmbeddingServiceError(
                f"Entrada inválida: {str(e)}",
                original_error=str(e)
            )
        except Exception as e:
            logger.error(
                "Error generando embedding síncrono",
                error=str(e),
                error_type=type(e).__name__,
                text_length=len(text) if text else 0
            )
            raise EmbeddingServiceError(
                "Error generando embedding síncrono para consulta",
                original_error=str(e)
            )
    
    def embed_documents_sync(self, texts: List[str]) -> List[List[float]]:
        """
        Versión síncrona de embed_documents para compatibilidad.
        
        Args:
            texts: Lista de textos a convertir en embeddings
            
        Returns:
            List[List[float]]: Lista de vectores de embedding
            
        Raises:
            EmbeddingServiceError: Si falla la generación de embeddings
        """
        try:
            if not texts:
                raise ValueError("La lista de textos no puede estar vacía")
            
            # Filtrar textos vacíos
            valid_texts = [text.strip() for text in texts if text and text.strip()]
            if not valid_texts:
                raise ValueError("No hay textos válidos para procesar")
            
            logger.info(
                "Generando embeddings síncronos para documentos",
                total_documents=len(valid_texts),
                avg_length=sum(len(text) for text in valid_texts) // len(valid_texts)
            )
            
            # Usar método síncrono de LangChain
            embeddings = self.embeddings.embed_documents(valid_texts)
            
            logger.info(
                "Embeddings síncronos generados exitosamente",
                documents_processed=len(embeddings),
                embedding_dimension=len(embeddings[0]) if embeddings else 0
            )
            
            return embeddings
            
        except ValueError as e:
            logger.warning(f"Entrada inválida para embeddings síncronos: {e}")
            raise EmbeddingServiceError(
                f"Entrada inválida: {str(e)}",
                original_error=str(e)
            )
        except Exception as e:
            logger.error(
                "Error generando embeddings síncronos para documentos",
                error=str(e),
                error_type=type(e).__name__,
                document_count=len(texts) if texts else 0
            )
            raise EmbeddingServiceError(
                "Error generando embeddings síncronos para documentos",
                original_error=str(e)
            )
    
    def get_embedding_dimension(self) -> int:
        """
        Obtiene la dimensión de los embeddings del proveedor actual.
        
        Returns:
            int: Dimensión de los embeddings
        """
        # Para text-embedding-3-small de OpenAI
        if isinstance(self.embeddings, OpenAIEmbeddings):
            return 1536
        
        # Para otros proveedores, intentar obtener la dimensión
        try:
            test_embedding = self.embed_query_sync("test")
            return len(test_embedding)
        except Exception:
            logger.warning("No se pudo determinar la dimensión de embeddings")
            return 1536  # Valor por defecto
    
    async def warmup(self) -> dict:
        """
        Realiza warm-up del servicio de embeddings para eliminar cold start.
        
        Returns:
            dict: Resultado del warm-up
        """
        try:
            logger.info("Iniciando warm-up del servicio de embeddings")
            start_time = time.time()
            
            # Realizar embedding de prueba para inicializar conexiones
            test_queries = [
                "test de conectividad",
                "configuración sistema",
                "búsqueda semántica"
            ]
            
            # Procesar embeddings de warm-up
            for i, query in enumerate(test_queries, 1):
                logger.debug(f"Warm-up {i}/{len(test_queries)}: '{query}'")
                await self.embed_query(query)
            
            duration = time.time() - start_time
            
            logger.info(
                "Warm-up completado exitosamente",
                duration=f"{duration:.3f}s",
                queries_processed=len(test_queries)
            )
            
            return {
                "status": "completed",
                "duration": duration,
                "queries_processed": len(test_queries),
                "provider": type(self.embeddings).__name__
            }
            
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            logger.error(
                "Error durante warm-up",
                error=str(e),
                duration=f"{duration:.3f}s"
            )
            return {
                "status": "failed",
                "error": str(e),
                "duration": duration,
                "provider": type(self.embeddings).__name__
            }
    
    def warmup_sync(self) -> dict:
        """
        Versión síncrona del warm-up para compatibilidad.
        
        Returns:
            dict: Resultado del warm-up
        """
        try:
            import time
            logger.info("Iniciando warm-up síncrono del servicio de embeddings")
            start_time = time.time()
            
            # Realizar embeddings de prueba
            test_queries = [
                "test de conectividad",
                "configuración sistema", 
                "búsqueda semántica"
            ]
            
            for i, query in enumerate(test_queries, 1):
                logger.debug(f"Warm-up síncrono {i}/{len(test_queries)}: '{query}'")
                self.embed_query_sync(query)
            
            duration = time.time() - start_time
            
            logger.info(
                "Warm-up síncrono completado exitosamente",
                duration=f"{duration:.3f}s",
                queries_processed=len(test_queries)
            )
            
            return {
                "status": "completed",
                "duration": duration,
                "queries_processed": len(test_queries),
                "provider": type(self.embeddings).__name__
            }
            
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            logger.error(
                "Error durante warm-up síncrono",
                error=str(e),
                duration=f"{duration:.3f}s"
            )
            return {
                "status": "failed",
                "error": str(e),
                "duration": duration,
                "provider": type(self.embeddings).__name__
            }
    
    def health_check(self) -> dict:
        """
        Verifica el estado del servicio de embeddings.
        
        Returns:
            dict: Estado del servicio
        """
        try:
            # Probar con un texto simple
            test_text = "test de conectividad"
            embedding = self.embed_query_sync(test_text)
            
            return {
                "status": "healthy",
                "provider": type(self.embeddings).__name__,
                "embedding_dimension": len(embedding),
                "test_successful": True
            }
            
        except Exception as e:
            logger.error(f"Health check falló: {e}")
            return {
                "status": "unhealthy",
                "provider": type(self.embeddings).__name__,
                "error": str(e),
                "test_successful": False
            }


# Instancia global del servicio
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Obtiene la instancia global del servicio de embeddings.
    Implementa patrón singleton para reutilizar la conexión.
    
    Returns:
        EmbeddingService: Instancia del servicio
    """
    global _embedding_service
    
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
        logger.info("Instancia global de EmbeddingService creada")
    
    return _embedding_service


def reset_embedding_service() -> None:
    """
    Resetea la instancia global del servicio.
    Útil para testing o reconfiguración.
    """
    global _embedding_service
    _embedding_service = None
    logger.info("Instancia global de EmbeddingService reseteada")