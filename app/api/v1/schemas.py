"""
Esquemas Pydantic para la API v1.
Define modelos de entrada y salida para endpoints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime


class SearchRequest(BaseModel):
    """Modelo para peticiones de búsqueda semántica."""
    
    pregunta: str = Field(
        ..., 
        description="Consulta en lenguaje natural",
        min_length=1,
        max_length=1000,
        example="¿dónde configuro alertas?"
    )
    
    top_k: int = Field(
        default=3,
        description="Número de resultados a retornar",
        ge=1,
        le=20,
        example=3
    )
    
    @field_validator('pregunta')
    @classmethod
    def validate_pregunta(cls, v):
        """Valida que la pregunta no esté vacía después de strip."""
        if not v.strip():
            raise ValueError('La pregunta no puede estar vacía')
        return v.strip()
    
    class Config:
        json_json_schema_extra = {
            "example": {
                "pregunta": "¿dónde configuro alertas del sistema?",
                "top_k": 3
            }
        }


class SearchResult(BaseModel):
    """Modelo para un resultado individual de búsqueda."""
    
    # Campos dinámicos del JSON original
    data: Dict[str, Any] = Field(
        ...,
        description="Datos originales del elemento encontrado"
    )
    
    # Score de similitud semántica (ahora obligatorio)
    score: float = Field(
        ...,
        description="Puntuación de similitud semántica (0-1, donde 1 es similitud perfecta)",
        ge=0.0,
        le=1.0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "ID": 2,
                    "Nivel0": "Configuración",
                    "Nivel1": "Alertas", 
                    "Descripcion": "Configura las notificaciones y alertas del sistema",
                    "url": "localhost/config/alertas"
                },
                "score": 0.8547
            }
        }


class SearchResponse(BaseModel):
    """Modelo para respuestas de búsqueda semántica."""
    
    resultados: List[SearchResult] = Field(
        ...,
        description="Lista de elementos encontrados ordenados por relevancia (score descendente)"
    )
    
    total: int = Field(
        ...,
        description="Número total de resultados encontrados",
        ge=0
    )
    
    tiempo_respuesta: float = Field(
        ...,
        description="Tiempo de procesamiento en segundos",
        ge=0.0
    )
    
    consulta: str = Field(
        ...,
        description="Consulta original procesada"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp de la respuesta"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "resultados": [
                    {
                        "data": {
                            "ID": 2,
                            "Nivel0": "Configuración",
                            "Nivel1": "Alertas",
                            "Descripcion": "Configura las notificaciones y alertas del sistema",
                            "url": "localhost/config/alertas"
                        },
                        "score": 0.8547
                    },
                    {
                        "data": {
                            "ID": 1,
                            "Nivel0": "Configuración", 
                            "Nivel1": "Sistema",
                            "Descripcion": "Configurar parámetros generales del sistema",
                            "url": "localhost/config/sistema"
                        },
                        "score": 0.6234
                    }
                ],
                "total": 2,
                "tiempo_respuesta": 0.245,
                "consulta": "¿dónde configuro alertas?",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Modelo para respuestas de health check."""
    
    status: str = Field(
        ...,
        description="Estado del servicio",
        example="healthy"
    )
    
    version: str = Field(
        ...,
        description="Versión de la API",
        example="1.0.0"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp del health check"
    )
    
    services: Optional[Dict[str, Any]] = Field(
        None,
        description="Estado de servicios externos"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0", 
                "timestamp": "2024-01-01T12:00:00Z",
                "services": {
                    "embedding_service": "healthy",
                    "vector_store": "healthy"
                }
            }
        }


class ErrorResponse(BaseModel):
    """Modelo para respuestas de error."""
    
    error: str = Field(
        ...,
        description="Código de error",
        example="VALIDATION_ERROR"
    )
    
    message: str = Field(
        ...,
        description="Mensaje descriptivo del error",
        example="La pregunta no puede estar vacía"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp del error"
    )
    
    path: Optional[str] = Field(
        None,
        description="Ruta del endpoint donde ocurrió el error",
        example="/v1/buscar"
    )
    
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Detalles adicionales del error"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "VALIDATION_ERROR",
                "message": "La pregunta no puede estar vacía",
                "timestamp": "2024-01-01T12:00:00Z",
                "path": "/v1/buscar",
                "details": {
                    "field": "pregunta"
                }
            }
        }


class IndexingRequest(BaseModel):
    """Modelo para peticiones de indexación (futuro uso)."""
    
    file_path: str = Field(
        ...,
        description="Ruta del archivo a indexar",
        example="data/menu.json"
    )
    
    force_rebuild: bool = Field(
        default=True,
        description="Forzar reconstrucción completa del índice"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "data/menu.json",
                "force_rebuild": True
            }
        }


class IndexingResponse(BaseModel):
    """Modelo para respuestas de indexación (futuro uso)."""
    
    status: str = Field(
        ...,
        description="Estado de la indexación",
        example="completed"
    )
    
    documents_processed: int = Field(
        ...,
        description="Número de documentos procesados",
        ge=0
    )
    
    processing_time: float = Field(
        ...,
        description="Tiempo de procesamiento en segundos",
        ge=0.0
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp de la indexación"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "documents_processed": 5,
                "processing_time": 12.34,
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


# Modelos de respuesta para diferentes códigos de estado HTTP
class ValidationErrorResponse(ErrorResponse):
    """Respuesta específica para errores de validación (422)."""
    
    error: str = Field(default="VALIDATION_ERROR")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "VALIDATION_ERROR",
                "message": "top_k debe estar entre 1 y 20",
                "timestamp": "2024-01-01T12:00:00Z",
                "path": "/v1/buscar",
                "details": {
                    "field": "top_k",
                    "value": 25
                }
            }
        }


class AuthenticationErrorResponse(ErrorResponse):
    """Respuesta específica para errores de autenticación (401)."""
    
    error: str = Field(default="AUTHENTICATION_REQUIRED")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "AUTHENTICATION_REQUIRED",
                "message": "Header X-API-Key requerido",
                "timestamp": "2024-01-01T12:00:00Z",
                "path": "/v1/buscar"
            }
        }


class AuthorizationErrorResponse(ErrorResponse):
    """Respuesta específica para errores de autorización (403)."""
    
    error: str = Field(default="INVALID_API_KEY")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "INVALID_API_KEY",
                "message": "Clave API inválida",
                "timestamp": "2024-01-01T12:00:00Z",
                "path": "/v1/buscar"
            }
        }


class ServiceUnavailableErrorResponse(ErrorResponse):
    """Respuesta específica para errores de servicio no disponible (503)."""
    
    error: str = Field(default="EXTERNAL_SERVICE_ERROR")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "EXTERNAL_SERVICE_ERROR",
                "message": "Servicio de embeddings no disponible temporalmente",
                "timestamp": "2024-01-01T12:00:00Z",
                "path": "/v1/buscar",
                "details": {
                    "service": "OpenAI Embeddings"
                }
            }
        }


# ============================================================================
# Schemas para endpoints de sincronización (saved_query)
# ============================================================================

class SavedQueryData(BaseModel):
    """Datos de saved_query para operaciones de sincronización."""
    
    id: int = Field(
        ..., 
        description="ID único de la consulta",
        gt=0,
        example=123
    )
    
    name: str = Field(
        ...,
        description="Nombre visible de la consulta",
        min_length=1,
        max_length=500,
        example="Reporte de ventas mensuales"
    )
    
    description: Optional[str] = Field(
        None,
        description="Descripción opcional de la consulta",
        max_length=2000,
        example="Consulta que genera reporte de ventas por mes y región"
    )
    
    query_sql_original: str = Field(
        ...,
        description="SQL original proporcionado por el usuario",
        example="SELECT * FROM sales WHERE month = ?"
    )
    
    query_sql_param: Optional[str] = Field(
        None,
        description="SQL parametrizado resultante",
        example="SELECT * FROM sales WHERE month = :month"
    )
    
    parameters_json: Optional[Dict[str, Any]] = Field(
        None,
        description="Estructura con metadatos de parámetros",
        example={"month": {"type": "integer", "default": 1}}
    )
    
    engine_code: str = Field(
        ...,
        description="Código del motor de base de datos",
        example="postgres"
    )
    
    company_id: int = Field(
        ...,
        description="ID de la compañía dueña de la consulta",
        example=456
    )
    
    owner_user_id: int = Field(
        ...,
        description="ID del usuario propietario",
        example=789
    )
    
    version: int = Field(
        default=1,
        description="Versión del registro",
        ge=1,
        example=1
    )
    
    is_active: bool = Field(
        default=True,
        description="Marca de vigencia de la consulta",
        example=True
    )
    
    created_at: datetime = Field(
        ...,
        description="Timestamp de creación",
        example="2024-01-15T10:30:00Z"
    )
    
    updated_at: datetime = Field(
        ...,
        description="Timestamp de última actualización",
        example="2024-01-15T10:30:00Z"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Valida que el nombre no esté vacío después de strip."""
        if not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "name": "Reporte de ventas mensuales",
                "description": "Consulta que genera reporte de ventas por mes",
                "query_sql_original": "SELECT * FROM sales WHERE month = ?",
                "query_sql_param": "SELECT * FROM sales WHERE month = :month",
                "parameters_json": {"month": {"type": "integer"}},
                "engine_code": "postgres",
                "company_id": 456,
                "owner_user_id": 789,
                "version": 1,
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class UpsertQueryRequest(BaseModel):
    """
    Request para operación de upsert de consulta.
    
    Contiene todos los datos necesarios para crear o actualizar una consulta
    guardada en la base de datos vectorial.
    """
    
    query: SavedQueryData = Field(
        ...,
        description="Datos completos de la consulta a sincronizar"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": {
                    "id": 123,
                    "name": "Reporte de ventas mensuales",
                    "description": "Consulta que genera reporte de ventas por mes y región",
                    "query_sql_original": "SELECT * FROM sales WHERE month = ?",
                    "query_sql_param": "SELECT * FROM sales WHERE month = :month",
                    "parameters_json": {"month": {"type": "integer", "default": 1}},
                    "engine_code": "postgres",
                    "company_id": 456,
                    "owner_user_id": 789,
                    "version": 1,
                    "is_active": True,
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z"
                }
            }
        }



class UpsertQueryResponse(BaseModel):
    """
    Response de operación de upsert.
    
    Confirma que la consulta fue sincronizada exitosamente en la base de datos vectorial.
    """
    
    id: int = Field(
        ...,
        description="ID de la consulta sincronizada",
        example=123
    )
    
    status: str = Field(
        default="success",
        description="Estado de la operación (success, updated, created)",
        example="success"
    )
    
    message: str = Field(
        default="Consulta sincronizada exitosamente",
        description="Mensaje descriptivo de la operación realizada",
        example="Consulta sincronizada exitosamente"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp UTC de cuando se completó la operación"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "status": "success",
                "message": "Consulta sincronizada exitosamente",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class QuerySearchResult(BaseModel):
    """
    Resultado individual de búsqueda de consultas guardadas.
    
    Contiene todos los metadatos de una consulta guardada más el score
    de similitud semántica con la consulta de búsqueda.
    """
    
    id: int = Field(..., description="ID único de la consulta")
    name: str = Field(..., description="Nombre visible de la consulta")
    description: Optional[str] = Field(None, description="Descripción opcional de la consulta")
    query_sql_original: str = Field(..., description="SQL original proporcionado por el usuario")
    query_sql_param: Optional[str] = Field(None, description="SQL parametrizado resultante")
    parameters_json: Optional[Dict[str, Any]] = Field(None, description="Estructura con metadatos de parámetros")
    engine_code: str = Field(..., description="Código del motor de base de datos (postgres, mysql, etc.)")
    company_id: int = Field(..., description="ID de la compañía dueña de la consulta")
    owner_user_id: int = Field(..., description="ID del usuario propietario de la consulta")
    version: int = Field(..., description="Versión del registro de la consulta")
    is_active: bool = Field(..., description="Marca de vigencia de la consulta (true=activa, false=inactiva)")
    created_at: str = Field(..., description="Timestamp de creación de la consulta")
    updated_at: str = Field(..., description="Timestamp de última actualización de la consulta")
    score: float = Field(
        ...,
        description="Puntuación de similitud semántica (0-1, donde 1 es similitud perfecta)",
        ge=0.0,
        le=1.0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "name": "Reporte de ventas mensuales",
                "description": "Consulta que genera reporte de ventas por mes y región",
                "query_sql_original": "SELECT * FROM sales WHERE month = ?",
                "query_sql_param": "SELECT * FROM sales WHERE month = :month",
                "parameters_json": {"month": {"type": "integer", "default": 1}},
                "engine_code": "postgres",
                "company_id": 456,
                "owner_user_id": 789,
                "version": 1,
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "score": 0.8547
            }
        }


class QuerySearchResponse(BaseModel):
    """Response de búsqueda de consultas guardadas."""
    
    resultados: List[QuerySearchResult] = Field(
        ...,
        description="Lista de consultas encontradas ordenadas por score"
    )
    
    total: int = Field(
        ...,
        description="Número total de resultados",
        ge=0
    )
    
    tiempo_respuesta: float = Field(
        ...,
        description="Tiempo de procesamiento en segundos",
        ge=0.0
    )
    
    consulta: str = Field(
        ...,
        description="Consulta original procesada"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp de la respuesta"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "resultados": [
                    {
                        "id": 123,
                        "name": "Reporte de ventas mensuales",
                        "description": "Consulta de ventas",
                        "query_sql_original": "SELECT * FROM sales",
                        "engine_code": "postgres",
                        "company_id": 456,
                        "owner_user_id": 789,
                        "version": 1,
                        "is_active": True,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z",
                        "score": 0.8547
                    }
                ],
                "total": 1,
                "tiempo_respuesta": 0.245,
                "consulta": "reportes de ventas mensuales",
                "timestamp": "2024-01-15T10:35:00Z"
            }
        }
