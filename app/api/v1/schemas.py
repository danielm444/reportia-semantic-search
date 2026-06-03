"""
Esquemas Pydantic para la API v1.
Define modelos de entrada y salida para endpoints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone


class SearchRequest(BaseModel):
    """Modelo para peticiones de búsqueda semántica."""

    pregunta: str = Field(
        ...,
        description="Consulta en lenguaje natural",
        min_length=1,
        max_length=1000,
        examples=["¿dónde configuro alertas?"]
    )

    top_k: int = Field(
        default=3,
        description="Número de resultados a retornar",
        ge=1,
        le=20,
        examples=[3]
    )

    score_threshold: Optional[float] = Field(
        default=None,
        description="Umbral mínimo de similitud (0-1). Filtra resultados por debajo.",
        ge=0.0,
        le=1.0,
        examples=[0.5]
    )

    filtros: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Filtros de igualdad sobre el payload. Cada par campo:valor se "
            "combina con AND; un valor de tipo lista coincide con cualquiera "
            "de sus elementos (OR)."
        ),
        examples=[{"tipo": "security", "estado": "active"}]
    )

    offset: int = Field(
        default=0,
        description="Número de resultados a saltar (paginación)",
        ge=0,
        examples=[0]
    )

    @field_validator('pregunta')
    @classmethod
    def validate_pregunta(cls, v):
        """Valida que la pregunta no esté vacía después de strip."""
        if not v.strip():
            raise ValueError('La pregunta no puede estar vacía')
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "pregunta": "¿dónde configuro alertas del sistema?",
                "top_k": 3,
                "score_threshold": 0.5,
                "filtros": {"tipo": "configuration"},
                "offset": 0
            }
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
    
    model_config = {
        "json_schema_extra": {
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
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp de la respuesta"
    )
    
    model_config = {
        "json_schema_extra": {
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
    }


class HealthResponse(BaseModel):
    """Modelo para respuestas de health check."""
    
    status: str = Field(
        ...,
        description="Estado del servicio",
        examples=["healthy"]
    )
    
    version: str = Field(
        ...,
        description="Versión de la API",
        examples=["1.0.0"]
    )
    
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp del health check"
    )
    
    services: Optional[Dict[str, Any]] = Field(
        None,
        description="Estado de servicios externos"
    )
    
    model_config = {
        "json_schema_extra": {
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
    }


class ErrorResponse(BaseModel):
    """Modelo para respuestas de error."""
    
    error: str = Field(
        ...,
        description="Código de error",
        examples=["VALIDATION_ERROR"]
    )
    
    message: str = Field(
        ...,
        description="Mensaje descriptivo del error",
        examples=["La pregunta no puede estar vacía"]
    )
    
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp del error"
    )
    
    path: Optional[str] = Field(
        None,
        description="Ruta del endpoint donde ocurrió el error",
        examples=["/v1/buscar"]
    )
    
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Detalles adicionales del error"
    )
    
    model_config = {
        "json_schema_extra": {
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
    }


class IndexingRequest(BaseModel):
    """Modelo para peticiones de indexación (futuro uso)."""
    
    file_path: str = Field(
        ...,
        description="Ruta del archivo a indexar",
        examples=["data/menu.json"]
    )
    
    force_rebuild: bool = Field(
        default=True,
        description="Forzar reconstrucción completa del índice"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "file_path": "data/menu.json",
                "force_rebuild": True
            }
        }
    }


class IndexingResponse(BaseModel):
    """Modelo para respuestas de indexación (futuro uso)."""
    
    status: str = Field(
        ...,
        description="Estado de la indexación",
        examples=["completed"]
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
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp de la indexación"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "completed",
                "documents_processed": 5,
                "processing_time": 12.34,
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }
    }


# Modelos de respuesta para diferentes códigos de estado HTTP
class ValidationErrorResponse(ErrorResponse):
    """Respuesta específica para errores de validación (422)."""
    
    error: str = Field(default="VALIDATION_ERROR")
    
    model_config = {
        "json_schema_extra": {
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
    }


class AuthenticationErrorResponse(ErrorResponse):
    """Respuesta específica para errores de autenticación (401)."""
    
    error: str = Field(default="AUTHENTICATION_REQUIRED")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "AUTHENTICATION_REQUIRED",
                "message": "Header X-API-Key requerido",
                "timestamp": "2024-01-01T12:00:00Z",
                "path": "/v1/buscar"
            }
        }
    }


class AuthorizationErrorResponse(ErrorResponse):
    """Respuesta específica para errores de autorización (403)."""
    
    error: str = Field(default="INVALID_API_KEY")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "INVALID_API_KEY",
                "message": "Clave API inválida",
                "timestamp": "2024-01-01T12:00:00Z",
                "path": "/v1/buscar"
            }
        }
    }


class ServiceUnavailableErrorResponse(ErrorResponse):
    """Respuesta específica para errores de servicio no disponible (503)."""
    
    error: str = Field(default="EXTERNAL_SERVICE_ERROR")
    
    model_config = {
        "json_schema_extra": {
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
        examples=[123]
    )
    
    name: str = Field(
        ...,
        description="Nombre visible de la consulta",
        min_length=1,
        max_length=500,
        examples=["Reporte de ventas mensuales"]
    )
    
    description: Optional[str] = Field(
        None,
        description="Descripción opcional de la consulta",
        max_length=2000,
        examples=["Consulta que genera reporte de ventas por mes y región"]
    )
    
    query_sql_original: str = Field(
        ...,
        description="SQL original proporcionado por el usuario",
        examples=["SELECT * FROM sales WHERE month = ?"]
    )
    
    query_sql_param: Optional[str] = Field(
        None,
        description="SQL parametrizado resultante",
        examples=["SELECT * FROM sales WHERE month = :month"]
    )
    
    parameters_json: Optional[Dict[str, Any]] = Field(
        None,
        description="Estructura con metadatos de parámetros",
        examples=[{"month": {"type": "integer", "default": 1}}]
    )
    
    engine_code: str = Field(
        ...,
        description="Código del motor de base de datos",
        examples=["postgres"]
    )
    
    company_id: int = Field(
        ...,
        description="ID de la compañía dueña de la consulta",
        examples=[456]
    )
    
    owner_user_id: int = Field(
        ...,
        description="ID del usuario propietario",
        examples=[789]
    )
    
    version: int = Field(
        default=1,
        description="Versión del registro",
        ge=1,
        examples=[1]
    )
    
    is_active: bool = Field(
        default=True,
        description="Marca de vigencia de la consulta",
        examples=[True]
    )
    
    created_at: datetime = Field(
        ...,
        description="Timestamp de creación",
        examples=["2024-01-15T10:30:00Z"]
    )
    
    updated_at: datetime = Field(
        ...,
        description="Timestamp de última actualización",
        examples=["2024-01-15T10:30:00Z"]
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Valida que el nombre no esté vacío después de strip."""
        if not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()
    
    model_config = {
        "json_schema_extra": {
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
    
    model_config = {
        "json_schema_extra": {
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
    }



class UpsertQueryResponse(BaseModel):
    """
    Response de operación de upsert.
    
    Confirma que la consulta fue sincronizada exitosamente en la base de datos vectorial.
    """
    
    id: int = Field(
        ...,
        description="ID de la consulta sincronizada",
        examples=[123]
    )
    
    status: str = Field(
        default="success",
        description="Estado de la operación (success, updated, created)",
        examples=["success"]
    )
    
    message: str = Field(
        default="Consulta sincronizada exitosamente",
        description="Mensaje descriptivo de la operación realizada",
        examples=["Consulta sincronizada exitosamente"]
    )
    
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp UTC de cuando se completó la operación"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 123,
                "status": "success",
                "message": "Consulta sincronizada exitosamente",
                "timestamp": "2024-01-15T10:30:00Z"
            }
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
    
    model_config = {
        "json_schema_extra": {
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
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp de la respuesta"
    )
    
    model_config = {
        "json_schema_extra": {
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
    }


# ============================================================================
# Schemas genéricos de documentos (núcleo agnóstico de dominio)
# ============================================================================

class DocumentData(BaseModel):
    """
    Documento genérico para indexar: id + texto a vectorizar + payload libre.

    El ``payload`` se almacena tal cual y se devuelve íntegro en las búsquedas,
    por lo que el servicio sirve para cualquier dominio (menú, saved queries…).
    """

    id: Union[int, str] = Field(
        ...,
        description="Identificador único del documento (entero o string)",
        examples=[42, "menu-usuarios"]
    )

    texto: str = Field(
        ...,
        description="Texto a vectorizar para la búsqueda semántica",
        min_length=1,
        examples=["Seguridad > Usuarios. Gestionar usuarios del sistema."]
    )

    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadatos arbitrarios a almacenar y devolver en búsquedas"
    )

    @field_validator('texto')
    @classmethod
    def validate_texto(cls, v):
        """Valida que el texto no esté vacío después de strip."""
        if not v.strip():
            raise ValueError('El texto no puede estar vacío')
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 42,
                "texto": "Seguridad > Usuarios. Gestionar usuarios del sistema.",
                "payload": {
                    "titulo": "Seguridad › Usuarios",
                    "url": "wwusersgam.aspx",
                    "tipo": "security"
                }
            }
        }
    }


class BatchDocumentUpsertRequest(BaseModel):
    """Request para upsert en lote de documentos genéricos."""

    documentos: List[DocumentData] = Field(
        ...,
        description="Lista de documentos a indexar",
        min_length=1
    )


class BatchUpsertQueryRequest(BaseModel):
    """Request para upsert en lote de consultas guardadas."""

    queries: List[SavedQueryData] = Field(
        ...,
        description="Lista de consultas guardadas a sincronizar",
        min_length=1
    )


class BatchUpsertResponse(BaseModel):
    """Response de operaciones de upsert en lote."""

    count: int = Field(..., description="Cantidad de elementos sincronizados", ge=0)
    ids: List[Union[int, str]] = Field(..., description="IDs de los elementos sincronizados")
    status: str = Field(default="success", description="Estado de la operación")
    message: str = Field(
        default="Sincronización en lote completada exitosamente",
        description="Mensaje descriptivo"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp UTC de la operación"
    )
