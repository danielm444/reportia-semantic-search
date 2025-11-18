"""
Router para endpoints de API v1.
Implementa búsqueda semántica y health checks.
"""

import time
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.api.v1.schemas import (
    SearchRequest, 
    SearchResponse, 
    HealthResponse,
    ErrorResponse,
    UpsertQueryRequest,
    UpsertQueryResponse,
    QuerySearchResult
)
from app.core.security import require_api_key
from fastapi.security.api_key import APIKeyHeader
from app.core.logging import get_logger
from app.core.exceptions import (
    SearchError, 
    EmbeddingServiceError, 
    VectorStoreError,
    QueryNotFoundError,
    QdrantConnectionError,
    QdrantOperationError
)
from app.services.search_service import get_search_service
from app.services.embedding_service import get_embedding_service
from app.config.settings import settings

logger = get_logger(__name__)

# Crear router para v1
router = APIRouter(prefix="/v1", tags=["API v1"])

# Esquema de seguridad para este router
api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verifica la API key."""
    if api_key != settings.menu_api_key:
        raise HTTPException(
            status_code=403,
            detail="Clave API inválida"
        )
    return api_key


@router.post(
    "/consultas/upsert",
    response_model=UpsertQueryResponse,
    responses={
        200: {
            "model": UpsertQueryResponse, 
            "description": "Consulta sincronizada exitosamente en la base de datos vectorial",
            "content": {
                "application/json": {
                    "example": {
                        "id": 123,
                        "status": "success",
                        "message": "Consulta sincronizada exitosamente",
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        422: {
            "model": ErrorResponse, 
            "description": "Error de validación en los datos de entrada",
            "content": {
                "application/json": {
                    "example": {
                        "error": "VALIDATION_ERROR",
                        "message": "El nombre no puede estar vacío",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "path": "/api/v1/consultas/upsert",
                        "details": {"field": "name"}
                    }
                }
            }
        },
        500: {
            "model": ErrorResponse, 
            "description": "Error interno del servidor",
            "content": {
                "application/json": {
                    "example": {
                        "error": "INTERNAL_SERVER_ERROR",
                        "message": "Error interno del servidor",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "path": "/api/v1/consultas/upsert"
                    }
                }
            }
        },
        503: {
            "model": ErrorResponse, 
            "description": "Servicio de base de datos vectorial no disponible",
            "content": {
                "application/json": {
                    "example": {
                        "error": "SERVICE_UNAVAILABLE",
                        "message": "Servicio de base de datos vectorial no disponible",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "path": "/api/v1/consultas/upsert",
                        "details": {"service": "Qdrant"}
                    }
                }
            }
        }
    },
    summary="Sincronizar consulta guardada",
    description="""
    Crea o actualiza una consulta guardada en la base de datos vectorial Qdrant.
    
    Este endpoint es llamado por el servicio `savedquery_service` cuando se crea o actualiza
    una consulta en la base de datos relacional, para mantener sincronizada la base de datos vectorial.
    
    **Flujo de operación:**
    1. Recibe los datos completos de la consulta guardada
    2. Combina `name` + `description` para generar texto indexable
    3. Genera embedding vectorial usando el servicio de embeddings
    4. Almacena el punto vectorial en Qdrant con todos los metadatos
    5. Retorna confirmación con el ID de la consulta sincronizada
    
    **Autenticación:**
    - Requiere header `X-API-Key` con una API key válida
    
    **Idempotencia:**
    - Si la consulta ya existe (mismo ID), se actualiza con los nuevos datos
    - Si no existe, se crea un nuevo punto vectorial
    
    **Casos de uso:**
    - Sincronización automática desde savedquery_service
    - Re-indexación manual de consultas existentes
    - Actualización de metadatos de consultas
    """
)
async def upsert_consulta(
    request: UpsertQueryRequest,
    api_key: str = Depends(verify_api_key)
) -> UpsertQueryResponse:
    """
    Endpoint de sincronización para crear o actualizar consultas guardadas.
    
    Este endpoint es llamado por savedquery_service cuando se crea o actualiza
    una consulta en la BD relacional, para mantener sincronizada la BD vectorial.
    """
    logger.info(
        "Iniciando upsert de consulta",
        query_id=request.query.id,
        query_name=request.query.name[:50]
    )
    
    try:
        # Obtener servicio de búsqueda
        search_service = get_search_service()
        
        # Convertir SavedQueryData a dict
        query_data = request.query.model_dump()
        
        # Realizar upsert
        result = await search_service.upsert_query(query_data)
        
        logger.info(
            "Upsert completado exitosamente",
            query_id=result["id"],
            query_name=request.query.name[:50]
        )
        
        return UpsertQueryResponse(
            id=result["id"],
            status=result["status"],
            message=result["message"]
        )
        
    except SearchError as e:
        logger.warning(
            "Error en upsert",
            error=e.message,
            query_id=request.query.id,
            error_code=e.error_code
        )
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except (QdrantConnectionError, QdrantOperationError) as e:
        logger.error(
            "Error de Qdrant en upsert",
            error=e.message,
            query_id=request.query.id
        )
        raise HTTPException(
            status_code=503,
            detail="Servicio de base de datos vectorial no disponible"
        )
    except Exception as e:
        logger.error(
            "Error inesperado en upsert",
            error=str(e),
            error_type=type(e).__name__,
            query_id=request.query.id,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.delete(
    "/consultas/{query_id}",
    status_code=204,
    responses={
        204: {
            "description": "Consulta eliminada exitosamente de la base de datos vectorial. No retorna contenido."
        },
        404: {
            "model": ErrorResponse, 
            "description": "Consulta no encontrada en la base de datos vectorial",
            "content": {
                "application/json": {
                    "example": {
                        "error": "QUERY_NOT_FOUND",
                        "message": "Consulta con ID 123 no encontrada",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "path": "/api/v1/consultas/123",
                        "details": {"query_id": 123}
                    }
                }
            }
        },
        422: {
            "model": ErrorResponse,
            "description": "ID de consulta inválido (debe ser un entero positivo)",
            "content": {
                "application/json": {
                    "example": {
                        "error": "VALIDATION_ERROR",
                        "message": "query_id debe ser un entero positivo",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "path": "/api/v1/consultas/-1",
                        "details": {"field": "query_id", "value": -1}
                    }
                }
            }
        },
        500: {
            "model": ErrorResponse,
            "description": "Error interno del servidor",
            "content": {
                "application/json": {
                    "example": {
                        "error": "INTERNAL_SERVER_ERROR",
                        "message": "Error interno del servidor",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "path": "/api/v1/consultas/123"
                    }
                }
            }
        },
        503: {
            "model": ErrorResponse, 
            "description": "Servicio de base de datos vectorial no disponible",
            "content": {
                "application/json": {
                    "example": {
                        "error": "SERVICE_UNAVAILABLE",
                        "message": "Servicio de base de datos vectorial no disponible",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "path": "/api/v1/consultas/123",
                        "details": {"service": "Qdrant"}
                    }
                }
            }
        }
    },
    summary="Eliminar consulta guardada",
    description="""
    Elimina una consulta guardada de la base de datos vectorial Qdrant.
    
    Este endpoint es llamado por el servicio `savedquery_service` cuando se elimina
    una consulta de la base de datos relacional, para mantener sincronizada la base de datos vectorial.
    
    **Flujo de operación:**
    1. Recibe el ID de la consulta a eliminar
    2. Valida que el ID sea un entero positivo
    3. Elimina el punto vectorial correspondiente de Qdrant
    4. Retorna código 204 (No Content) si la eliminación fue exitosa
    5. Retorna código 404 si la consulta no existe
    
    **Autenticación:**
    - Requiere header `X-API-Key` con una API key válida
    
    **Idempotencia:**
    - Si la consulta no existe, retorna 404
    - Múltiples llamadas con el mismo ID retornarán 404 después de la primera eliminación exitosa
    
    **Casos de uso:**
    - Sincronización automática desde savedquery_service
    - Limpieza manual de consultas obsoletas
    - Mantenimiento de la base de datos vectorial
    
    **Parámetros:**
    - `query_id` (path): ID único de la consulta a eliminar (entero positivo)
    """
)
async def delete_consulta(
    query_id: int,
    api_key: str = Depends(verify_api_key)
):
    """
    Endpoint de sincronización para eliminar consultas guardadas.
    
    Este endpoint es llamado por savedquery_service cuando se elimina
    una consulta de la BD relacional, para mantener sincronizada la BD vectorial.
    """
    logger.info(
        "Iniciando eliminación de consulta",
        query_id=query_id
    )
    
    try:
        # Obtener servicio de búsqueda
        search_service = get_search_service()
        
        # Realizar eliminación
        await search_service.delete_query(query_id)
        
        logger.info(
            "Consulta eliminada exitosamente",
            query_id=query_id
        )
        
        # Retornar 204 No Content
        return JSONResponse(status_code=204, content=None)
        
    except QueryNotFoundError as e:
        logger.warning(
            "Consulta no encontrada para eliminar",
            query_id=query_id
        )
        raise HTTPException(
            status_code=404,
            detail=e.message
        )
    except (QdrantConnectionError, QdrantOperationError) as e:
        logger.error(
            "Error de Qdrant en eliminación",
            error=e.message,
            query_id=query_id
        )
        raise HTTPException(
            status_code=503,
            detail="Servicio de base de datos vectorial no disponible"
        )
    except Exception as e:
        logger.error(
            "Error inesperado en eliminación",
            error=str(e),
            error_type=type(e).__name__,
            query_id=query_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.post(
    "/buscar",
    response_model=SearchResponse,
    responses={
        200: {
            "model": SearchResponse,
            "description": "Búsqueda completada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "resultados": [
                            {
                                "data": {
                                    "id": 123,
                                    "name": "Reporte de ventas mensuales",
                                    "description": "Consulta que genera reporte de ventas por mes",
                                    "query_sql_original": "SELECT * FROM sales WHERE month = ?",
                                    "company_id": 456,
                                    "owner_user_id": 789,
                                    "is_active": True,
                                    "created_at": "2024-01-15T10:30:00Z",
                                    "updated_at": "2024-01-15T10:30:00Z"
                                },
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
        },
        400: {
            "model": ErrorResponse, 
            "description": "Petición inválida o mal formada",
            "content": {
                "application/json": {
                    "example": {
                        "error": "BAD_REQUEST",
                        "message": "Formato de petición inválido",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "path": "/api/v1/buscar"
                    }
                }
            }
        },
        401: {
            "model": ErrorResponse, 
            "description": "Autenticación requerida - falta header X-API-Key",
            "content": {
                "application/json": {
                    "example": {
                        "error": "AUTHENTICATION_REQUIRED",
                        "message": "Header X-API-Key requerido",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "path": "/api/v1/buscar"
                    }
                }
            }
        },
        403: {
            "model": ErrorResponse, 
            "description": "Clave API inválida o sin permisos",
            "content": {
                "application/json": {
                    "example": {
                        "error": "INVALID_API_KEY",
                        "message": "Clave API inválida",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "path": "/api/v1/buscar"
                    }
                }
            }
        },
        422: {
            "model": ErrorResponse, 
            "description": "Error de validación en los parámetros de búsqueda",
            "content": {
                "application/json": {
                    "example": {
                        "error": "VALIDATION_ERROR",
                        "message": "La pregunta no puede estar vacía",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "path": "/api/v1/buscar",
                        "details": {"field": "pregunta"}
                    }
                }
            }
        },
        500: {
            "model": ErrorResponse,
            "description": "Error interno del servidor",
            "content": {
                "application/json": {
                    "example": {
                        "error": "INTERNAL_SERVER_ERROR",
                        "message": "Error interno del servidor",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "path": "/api/v1/buscar"
                    }
                }
            }
        },
        503: {
            "model": ErrorResponse, 
            "description": "Servicio de búsqueda o embeddings no disponible",
            "content": {
                "application/json": {
                    "example": {
                        "error": "SERVICE_UNAVAILABLE",
                        "message": "Servicio de búsqueda no disponible temporalmente",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "path": "/api/v1/buscar",
                        "details": {"service": "OpenAI Embeddings"}
                    }
                }
            }
        }
    },
    summary="Búsqueda semántica de consultas guardadas",
    description="""
    Realiza búsqueda semántica sobre consultas guardadas usando lenguaje natural.
    
    Este endpoint permite buscar consultas guardadas utilizando similitud semántica vectorial.
    Recibe una consulta en lenguaje natural y retorna las consultas más relevantes ordenadas
    por score de similitud.
    
    **Flujo de operación:**
    1. Recibe la consulta en lenguaje natural del usuario
    2. Genera embedding vectorial de la consulta usando el servicio de embeddings
    3. Realiza búsqueda de similitud vectorial en Qdrant
    4. Retorna los resultados ordenados por score de similitud (descendente)
    5. Incluye todos los metadatos de cada consulta guardada
    
    **Autenticación:**
    - Requiere header `X-API-Key` con una API key válida
    
    **Parámetros de búsqueda:**
    - `pregunta` (string): Consulta en lenguaje natural (1-1000 caracteres)
    - `top_k` (integer): Número de resultados a retornar (1-20, default: 3)
    
    **Formato de resultados:**
    Cada resultado incluye:
    - `data`: Objeto con todos los campos de la consulta guardada
      - `id`: ID único de la consulta
      - `name`: Nombre de la consulta
      - `description`: Descripción opcional
      - `query_sql_original`: SQL original
      - `query_sql_param`: SQL parametrizado
      - `parameters_json`: Metadatos de parámetros
      - `engine_code`: Motor de base de datos
      - `company_id`: ID de compañía
      - `owner_user_id`: ID de usuario propietario
      - `version`: Versión del registro
      - `is_active`: Estado activo/inactivo
      - `created_at`: Fecha de creación
      - `updated_at`: Fecha de última actualización
    - `score`: Puntuación de similitud semántica (0-1, donde 1 es similitud perfecta)
    
    **Casos de uso:**
    - Búsqueda de consultas por descripción natural
    - Descubrimiento de consultas similares
    - Recomendación de consultas relacionadas
    - Exploración del catálogo de consultas
    
    **Ejemplos de consultas:**
    - "reportes de ventas mensuales"
    - "consultas de inventario por producto"
    - "análisis de clientes activos"
    """
)
async def buscar(
    request: SearchRequest,
    api_key: str = Depends(verify_api_key)
) -> SearchResponse:
    """
    Endpoint principal de búsqueda semántica.
    
    Recibe una consulta en lenguaje natural y retorna los elementos
    más relevantes del catálogo ordenados por similitud semántica.
    """
    start_time = time.time()
    
    logger.info(
        "Iniciando búsqueda semántica",
        query=request.pregunta,
        top_k=request.top_k,
        query_length=len(request.pregunta)
    )
    
    try:
        # Obtener servicio de búsqueda
        search_service = get_search_service()
        
        # Realizar búsqueda
        resultados_raw = await search_service.search(
            query=request.pregunta,
            top_k=request.top_k
        )
        
        # Calcular tiempo de respuesta
        tiempo_respuesta = time.time() - start_time
        
        # Convertir resultados al formato SearchResult
        # Los resultados ya vienen con la estructura correcta desde SearchService
        from app.api.v1.schemas import SearchResult
        resultados = [
            SearchResult(data=resultado["data"], score=resultado["score"])
            for resultado in resultados_raw
        ]
        
        # Crear respuesta
        response = SearchResponse(
            resultados=resultados,
            total=len(resultados),
            tiempo_respuesta=tiempo_respuesta,
            consulta=request.pregunta
        )
        
        logger.info(
            "Búsqueda completada exitosamente",
            results_count=len(resultados),
            processing_time=tiempo_respuesta,
            query=request.pregunta
        )
        
        return response
        
    except SearchError as e:
        logger.warning(
            "Error de búsqueda",
            error=e.message,
            query=request.pregunta,
            error_code=e.error_code
        )
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except (EmbeddingServiceError, VectorStoreError) as e:
        logger.error(
            "Error de servicio externo",
            error=e.message,
            service=e.details.get('service', 'unknown'),
            query=request.pregunta
        )
        raise HTTPException(
            status_code=503,
            detail="Servicio de búsqueda no disponible temporalmente"
        )
    except Exception as e:
        logger.error(
            "Error inesperado en búsqueda",
            error=str(e),
            error_type=type(e).__name__,
            query=request.pregunta,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Verifica el estado del servicio y sus dependencias"
)
async def health_check() -> HealthResponse:
    """
    Endpoint de health check para monitoreo.
    
    Verifica el estado del servicio de búsqueda y sus dependencias
    como el servicio de embeddings y la base de datos vectorial.
    """
    logger.info("Health check solicitado")
    
    try:
        # Verificar servicios
        embedding_service = get_embedding_service()
        search_service = get_search_service()
        
        # Obtener estado de servicios
        embedding_health = embedding_service.health_check()
        search_health = search_service.health_check()
        
        # Extraer información de Qdrant del search_health
        qdrant_health = search_health.get("qdrant", {})
        
        # Determinar estado general
        overall_status = "healthy"
        if (embedding_health.get("status") != "healthy" or 
            search_health.get("status") != "healthy" or
            qdrant_health.get("status") != "healthy"):
            overall_status = "degraded"
        
        # Crear respuesta con información detallada de Qdrant
        response = HealthResponse(
            status=overall_status,
            version=settings.app_version,
            services={
                "embedding_service": {
                    "status": embedding_health.get("status", "unknown"),
                    "provider": embedding_health.get("provider", "unknown")
                },
                "qdrant": {
                    "status": qdrant_health.get("status", "unknown"),
                    "url": qdrant_health.get("url", "unknown"),
                    "collection_name": qdrant_health.get("collection_name", "unknown"),
                    "collection_exists": qdrant_health.get("collection_exists", False),
                    "collection_info": qdrant_health.get("collection_info", {})
                },
                "search_service": {
                    "status": search_health.get("status", "unknown")
                }
            }
        )
        
        logger.info(
            "Health check completado",
            overall_status=overall_status,
            embedding_status=embedding_health.get("status"),
            qdrant_status=qdrant_health.get("status"),
            search_status=search_health.get("status")
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Error en health check",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        
        # Retornar estado unhealthy pero no fallar
        return HealthResponse(
            status="unhealthy",
            version=settings.app_version,
            services={
                "error": str(e)
            }
        )


@router.get(
    "/info",
    summary="Información de la API",
    description="Información general sobre la API v1, endpoints disponibles y capacidades"
)
async def api_info() -> Dict[str, Any]:
    """
    Endpoint informativo sobre la API v1.
    
    Proporciona información básica sobre la versión,
    configuración y capacidades de la API.
    """
    logger.info("Información de API solicitada")
    
    try:
        search_service = get_search_service()
        collection_info = search_service.get_collection_info()
        
        return {
            "api_version": "v1",
            "app_version": settings.app_version,
            "app_name": settings.app_name,
            "endpoints": {
                "search": {
                    "path": "/v1/buscar",
                    "method": "POST",
                    "description": "Búsqueda semántica de consultas guardadas"
                },
                "upsert": {
                    "path": "/v1/consultas/upsert",
                    "method": "POST",
                    "description": "Crear o actualizar consulta guardada"
                },
                "delete": {
                    "path": "/v1/consultas/{query_id}",
                    "method": "DELETE",
                    "description": "Eliminar consulta guardada"
                },
                "health": {
                    "path": "/v1/health",
                    "method": "GET",
                    "description": "Health check detallado"
                },
                "info": {
                    "path": "/v1/info",
                    "method": "GET",
                    "description": "Información de la API"
                }
            },
            "search_capabilities": {
                "max_results": 20,
                "max_query_length": 1000,
                "supported_languages": ["es", "en"],
                "vector_store": "Qdrant",
                "embedding_model": "text-embedding-3-small"
            },
            "sync_capabilities": {
                "upsert": "Sincronización automática desde savedquery_service",
                "delete": "Eliminación sincronizada con BD relacional",
                "idempotent": True
            },
            "collection_info": collection_info,
            "authentication": {
                "type": "API Key",
                "header": "X-API-Key",
                "required": True
            },
            "documentation": "/docs"
        }
        
    except Exception as e:
        logger.warning(f"Error obteniendo información: {e}")
        return {
            "api_version": "v1",
            "app_version": settings.app_version,
            "app_name": settings.app_name,
            "status": "partial_info",
            "error": "No se pudo obtener información completa"
        }