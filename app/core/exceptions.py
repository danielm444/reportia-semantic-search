"""
Excepciones personalizadas para el sistema MENU.
Define errores específicos del dominio y manejo estructurado.
"""

from typing import Any, Dict, Optional
from datetime import datetime


class MenuAPIException(Exception):
    """Excepción base para errores de la API MENU."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la excepción a diccionario para respuesta JSON."""
        return {
            "error": self.error_code,
            "message": self.message,
            "timestamp": self.timestamp,
            "details": self.details
        }


class ConfigurationError(MenuAPIException):
    """Error de configuración del sistema."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="CONFIGURATION_ERROR",
            details=details
        )


class AuthenticationError(MenuAPIException):
    """Error de autenticación."""
    
    def __init__(self, message: str = "Autenticación requerida"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_REQUIRED"
        )


class AuthorizationError(MenuAPIException):
    """Error de autorización."""
    
    def __init__(self, message: str = "Clave API inválida"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="INVALID_API_KEY"
        )


class ValidationError(MenuAPIException):
    """Error de validación de datos."""
    
    def __init__(self, message: str, field: str = None):
        details = {"field": field} if field else {}
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details
        )


class ExternalServiceError(MenuAPIException):
    """Error de servicio externo (OpenAI, ChromaDB, etc.)."""
    
    def __init__(self, service: str, message: str, original_error: str = None):
        details = {
            "service": service,
            "original_error": original_error
        }
        super().__init__(
            message=f"Error en servicio {service}: {message}",
            status_code=503,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details
        )


class EmbeddingServiceError(ExternalServiceError):
    """Error específico del servicio de embeddings."""
    
    def __init__(self, message: str, original_error: str = None):
        super().__init__(
            service="OpenAI Embeddings",
            message=message,
            original_error=original_error
        )


class VectorStoreError(ExternalServiceError):
    """Error específico de la base de datos vectorial."""
    
    def __init__(self, message: str, original_error: str = None):
        super().__init__(
            service="ChromaDB",
            message=message,
            original_error=original_error
        )


class SearchError(MenuAPIException):
    """Error durante operaciones de búsqueda."""
    
    def __init__(self, message: str, query: str = None):
        details = {"query": query} if query else {}
        super().__init__(
            message=message,
            status_code=400,
            error_code="SEARCH_ERROR",
            details=details
        )


class IndexingError(MenuAPIException):
    """Error durante operaciones de indexación."""
    
    def __init__(self, message: str, file_path: str = None):
        details = {"file_path": file_path} if file_path else {}
        super().__init__(
            message=message,
            status_code=500,
            error_code="INDEXING_ERROR",
            details=details
        )


class QdrantConnectionError(MenuAPIException):
    """Error de conexión con Qdrant."""
    
    def __init__(self, message: str = "Error conectando con Qdrant", url: str = None):
        details = {"url": url} if url else {}
        super().__init__(
            message=message,
            status_code=503,
            error_code="QDRANT_CONNECTION_ERROR",
            details=details
        )


class QdrantOperationError(MenuAPIException):
    """Error en operación de Qdrant."""
    
    def __init__(self, operation: str, details_msg: str, collection: str = None):
        details = {
            "operation": operation,
            "error": details_msg
        }
        if collection:
            details["collection"] = collection
        
        super().__init__(
            message=f"Error en operación de Qdrant: {operation}",
            status_code=500,
            error_code="QDRANT_OPERATION_ERROR",
            details=details
        )


class QueryNotFoundError(MenuAPIException):
    """Consulta no encontrada en la base de datos vectorial."""
    
    def __init__(self, query_id: int):
        super().__init__(
            message=f"Consulta con ID {query_id} no encontrada",
            status_code=404,
            error_code="QUERY_NOT_FOUND",
            details={"query_id": query_id}
        )