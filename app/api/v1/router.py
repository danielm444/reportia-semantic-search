"""
Router para endpoints de API v1.

Expone:
- Búsqueda semántica (`/buscar`) con filtros, umbral de score y paginación.
- API genérica de documentos (`/documentos/...`).
- Adaptadores de compatibilidad para saved queries (`/consultas/...`).
- Health check e info.
"""

import time
from typing import Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.api.v1.schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    HealthResponse,
    ErrorResponse,
    UpsertQueryRequest,
    UpsertQueryResponse,
    DocumentData,
    BatchDocumentUpsertRequest,
    BatchUpsertQueryRequest,
    BatchUpsertResponse,
)
from app.core.security import get_api_key
from app.core.logging import get_logger
from app.core.exceptions import (
    SearchError,
    EmbeddingServiceError,
    VectorStoreError,
    QueryNotFoundError,
    QdrantConnectionError,
    QdrantOperationError,
)
from app.services.search_service import get_search_service
from app.services.embedding_service import get_embedding_service
from app.config.settings import settings

logger = get_logger(__name__)

# Crear router para v1
router = APIRouter(prefix="/v1", tags=["API v1"])


# ============================================================================
# Búsqueda semántica
# ============================================================================

@router.post(
    "/buscar",
    response_model=SearchResponse,
    summary="Búsqueda semántica",
    description="""
    Realiza búsqueda semántica sobre los documentos indexados usando lenguaje natural.

    Cada resultado incluye `data` con el **payload completo** del documento
    (cualquier estructura indexada) y un `score` de similitud (0-1, descendente).

    Parámetros opcionales:
    - `score_threshold`: descarta resultados por debajo del umbral.
    - `filtros`: igualdad sobre el payload (AND entre campos; lista = OR).
    - `offset`: paginación.

    Requiere header `X-API-Key`.
    """,
)
async def buscar(
    request: SearchRequest,
    api_key: str = Depends(get_api_key),
) -> SearchResponse:
    """Endpoint principal de búsqueda semántica."""
    start_time = time.time()

    logger.info(
        "Iniciando búsqueda semántica",
        query=request.pregunta,
        top_k=request.top_k,
        has_filters=bool(request.filtros),
        score_threshold=request.score_threshold,
        offset=request.offset,
    )

    try:
        search_service = get_search_service()

        resultados_raw = await search_service.search(
            query=request.pregunta,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            filters=request.filtros,
            offset=request.offset,
        )

        resultados = [
            SearchResult(data=r["data"], score=r["score"])
            for r in resultados_raw
        ]

        response = SearchResponse(
            resultados=resultados,
            total=len(resultados),
            tiempo_respuesta=time.time() - start_time,
            consulta=request.pregunta,
        )

        logger.info(
            "Búsqueda completada exitosamente",
            results_count=len(resultados),
            processing_time=response.tiempo_respuesta,
        )
        return response

    except SearchError as e:
        logger.warning("Error de búsqueda", error=e.message, error_code=e.error_code)
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except (EmbeddingServiceError, VectorStoreError) as e:
        logger.error("Error de servicio externo", error=e.message)
        raise HTTPException(
            status_code=503,
            detail="Servicio de búsqueda no disponible temporalmente",
        )
    except Exception as e:
        logger.error(
            "Error inesperado en búsqueda",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ============================================================================
# API genérica de documentos
# ============================================================================

@router.post(
    "/documentos/upsert",
    response_model=BatchUpsertResponse,
    summary="Indexar un documento genérico",
    description="""
    Crea o actualiza un documento genérico (`id` + `texto` + `payload` libre)
    en la base de datos vectorial. El `payload` se devuelve íntegro en las
    búsquedas. Requiere header `X-API-Key`.
    """,
    responses={
        422: {"model": ErrorResponse, "description": "Error de validación"},
        503: {"model": ErrorResponse, "description": "Servicio vectorial no disponible"},
    },
)
async def upsert_documento(
    documento: DocumentData,
    api_key: str = Depends(get_api_key),
) -> BatchUpsertResponse:
    """Indexa un único documento genérico."""
    logger.info("Upsert de documento", doc_id=documento.id)
    try:
        search_service = get_search_service()
        result = await search_service.upsert_document(
            doc_id=documento.id,
            text=documento.texto,
            payload=documento.payload,
        )
        return BatchUpsertResponse(
            count=1,
            ids=[result["id"]],
            message="Documento sincronizado exitosamente",
        )
    except SearchError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except (QdrantConnectionError, QdrantOperationError):
        raise HTTPException(status_code=503, detail="Servicio de base de datos vectorial no disponible")
    except Exception as e:
        logger.error("Error inesperado en upsert de documento", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post(
    "/documentos/upsert/batch",
    response_model=BatchUpsertResponse,
    summary="Indexar documentos genéricos en lote",
    description="""
    Crea o actualiza múltiples documentos genéricos en una sola operación
    (embeddings y upsert en lote). Requiere header `X-API-Key`.
    """,
    responses={
        422: {"model": ErrorResponse, "description": "Error de validación"},
        503: {"model": ErrorResponse, "description": "Servicio vectorial no disponible"},
    },
)
async def upsert_documentos_batch(
    request: BatchDocumentUpsertRequest,
    api_key: str = Depends(get_api_key),
) -> BatchUpsertResponse:
    """Indexa documentos genéricos en lote."""
    logger.info("Upsert de documentos en lote", count=len(request.documentos))
    try:
        search_service = get_search_service()
        documents = [
            {"id": d.id, "texto": d.texto, "payload": d.payload}
            for d in request.documentos
        ]
        result = await search_service.upsert_documents(documents)
        return BatchUpsertResponse(count=result["count"], ids=result["ids"])
    except SearchError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except (QdrantConnectionError, QdrantOperationError):
        raise HTTPException(status_code=503, detail="Servicio de base de datos vectorial no disponible")
    except Exception as e:
        logger.error("Error inesperado en upsert en lote", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.delete(
    "/documentos/{doc_id}",
    status_code=204,
    summary="Eliminar un documento genérico",
    description="Elimina un documento por su id (entero o string). Requiere `X-API-Key`.",
    responses={
        204: {"description": "Documento eliminado exitosamente"},
        404: {"model": ErrorResponse, "description": "Documento no encontrado"},
        503: {"model": ErrorResponse, "description": "Servicio vectorial no disponible"},
    },
)
async def delete_documento(
    doc_id: str,
    api_key: str = Depends(get_api_key),
):
    """Elimina un documento genérico por id."""
    # Coercionar a int si el path es numérico (consistencia con la indexación)
    coerced: Union[int, str] = int(doc_id) if doc_id.lstrip("-").isdigit() else doc_id
    logger.info("Eliminando documento", doc_id=coerced)
    try:
        search_service = get_search_service()
        deleted = search_service.delete_document(coerced)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Documento '{coerced}' no encontrado")
        return JSONResponse(status_code=204, content=None)
    except HTTPException:
        raise
    except SearchError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except (QdrantConnectionError, QdrantOperationError):
        raise HTTPException(status_code=503, detail="Servicio de base de datos vectorial no disponible")
    except Exception as e:
        logger.error("Error inesperado eliminando documento", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ============================================================================
# Compatibilidad: saved queries
# ============================================================================

@router.post(
    "/consultas/upsert",
    response_model=UpsertQueryResponse,
    summary="Sincronizar consulta guardada",
    description="""
    Crea o actualiza una consulta guardada (saved_query) en la base vectorial.
    Combina `name` + `description` como texto indexable y almacena todos los
    metadatos. Adaptador sobre el núcleo genérico. Requiere `X-API-Key`.
    """,
    responses={
        422: {"model": ErrorResponse, "description": "Error de validación"},
        503: {"model": ErrorResponse, "description": "Servicio vectorial no disponible"},
    },
)
async def upsert_consulta(
    request: UpsertQueryRequest,
    api_key: str = Depends(get_api_key),
) -> UpsertQueryResponse:
    """Crea o actualiza una consulta guardada."""
    logger.info("Upsert de consulta", query_id=request.query.id)
    try:
        search_service = get_search_service()
        result = await search_service.upsert_query(request.query.model_dump())
        return UpsertQueryResponse(
            id=result["id"],
            status=result["status"],
            message=result["message"],
        )
    except SearchError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except (QdrantConnectionError, QdrantOperationError):
        raise HTTPException(status_code=503, detail="Servicio de base de datos vectorial no disponible")
    except Exception as e:
        logger.error("Error inesperado en upsert de consulta", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post(
    "/consultas/upsert/batch",
    response_model=BatchUpsertResponse,
    summary="Sincronizar consultas guardadas en lote",
    description="Crea o actualiza múltiples consultas guardadas en una operación. Requiere `X-API-Key`.",
    responses={
        422: {"model": ErrorResponse, "description": "Error de validación"},
        503: {"model": ErrorResponse, "description": "Servicio vectorial no disponible"},
    },
)
async def upsert_consultas_batch(
    request: BatchUpsertQueryRequest,
    api_key: str = Depends(get_api_key),
) -> BatchUpsertResponse:
    """Sincroniza consultas guardadas en lote."""
    logger.info("Upsert de consultas en lote", count=len(request.queries))
    try:
        search_service = get_search_service()
        result = await search_service.upsert_queries(
            [q.model_dump() for q in request.queries]
        )
        return BatchUpsertResponse(count=result["count"], ids=result["ids"])
    except SearchError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except (QdrantConnectionError, QdrantOperationError):
        raise HTTPException(status_code=503, detail="Servicio de base de datos vectorial no disponible")
    except Exception as e:
        logger.error("Error inesperado en upsert de consultas en lote", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.delete(
    "/consultas/{query_id}",
    status_code=204,
    summary="Eliminar consulta guardada",
    description="Elimina una consulta guardada por su ID. Requiere `X-API-Key`.",
    responses={
        204: {"description": "Consulta eliminada exitosamente"},
        404: {"model": ErrorResponse, "description": "Consulta no encontrada"},
        503: {"model": ErrorResponse, "description": "Servicio vectorial no disponible"},
    },
)
async def delete_consulta(
    query_id: int,
    api_key: str = Depends(get_api_key),
):
    """Elimina una consulta guardada por ID."""
    logger.info("Eliminando consulta", query_id=query_id)
    try:
        search_service = get_search_service()
        await search_service.delete_query(query_id)
        return JSONResponse(status_code=204, content=None)
    except QueryNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except (QdrantConnectionError, QdrantOperationError):
        raise HTTPException(status_code=503, detail="Servicio de base de datos vectorial no disponible")
    except SearchError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error("Error inesperado eliminando consulta", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ============================================================================
# Diagnóstico
# ============================================================================

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Verifica el estado del servicio y sus dependencias (Qdrant y embeddings).",
)
async def health_check() -> HealthResponse:
    """Health check detallado del servicio y dependencias."""
    logger.info("Health check solicitado")
    try:
        embedding_service = get_embedding_service()
        search_service = get_search_service()

        embedding_health = embedding_service.health_check()
        search_health = search_service.health_check()
        qdrant_health = search_health.get("qdrant", {})

        overall_status = "healthy"
        if (embedding_health.get("status") != "healthy" or
                search_health.get("status") != "healthy" or
                qdrant_health.get("status") != "healthy"):
            overall_status = "degraded"

        return HealthResponse(
            status=overall_status,
            version=settings.app_version,
            services={
                "embedding_service": {
                    "status": embedding_health.get("status", "unknown"),
                    "provider": embedding_health.get("provider", "unknown"),
                },
                "qdrant": {
                    "status": qdrant_health.get("status", "unknown"),
                    "url": qdrant_health.get("url", "unknown"),
                    "collection_name": qdrant_health.get("collection_name", "unknown"),
                    "collection_exists": qdrant_health.get("collection_exists", False),
                    "collection_info": qdrant_health.get("collection_info", {}),
                },
                "search_service": {"status": search_health.get("status", "unknown")},
            },
        )
    except Exception as e:
        logger.error("Error en health check", error=str(e), exc_info=True)
        return HealthResponse(
            status="unhealthy",
            version=settings.app_version,
            services={"error": str(e)},
        )


@router.get(
    "/info",
    summary="Información de la API",
    description="Información general sobre la API v1, endpoints y capacidades.",
)
async def api_info() -> Dict[str, Any]:
    """Información sobre la API v1."""
    logger.info("Información de API solicitada")
    try:
        search_service = get_search_service()
        collection_info = search_service.get_collection_info()
    except Exception as e:
        logger.warning(f"No se pudo obtener info de colección: {e}")
        collection_info = {"error": "No disponible"}

    return {
        "api_version": "v1",
        "app_version": settings.app_version,
        "app_name": settings.app_name,
        "endpoints": {
            "search": {"path": "/v1/buscar", "method": "POST"},
            "documento_upsert": {"path": "/v1/documentos/upsert", "method": "POST"},
            "documento_upsert_batch": {"path": "/v1/documentos/upsert/batch", "method": "POST"},
            "documento_delete": {"path": "/v1/documentos/{doc_id}", "method": "DELETE"},
            "consulta_upsert": {"path": "/v1/consultas/upsert", "method": "POST"},
            "consulta_upsert_batch": {"path": "/v1/consultas/upsert/batch", "method": "POST"},
            "consulta_delete": {"path": "/v1/consultas/{query_id}", "method": "DELETE"},
            "health": {"path": "/v1/health", "method": "GET"},
            "info": {"path": "/v1/info", "method": "GET"},
        },
        "search_capabilities": {
            "max_results": 20,
            "max_query_length": 1000,
            "filters": True,
            "score_threshold": True,
            "pagination": True,
            "vector_store": "Qdrant",
            "embedding_model": "text-embedding-3-small",
        },
        "collection_info": collection_info,
        "authentication": {"type": "API Key", "header": "X-API-Key", "required": True},
        "documentation": "/docs",
    }
