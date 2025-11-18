"""
Punto de entrada principal para la API de Búsqueda Semántica MENU.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time
from app.config.settings import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import MenuAPIException, AuthenticationError, AuthorizationError
from app.core.security import SecurityHeaders, validate_request_size, get_client_ip
from app.api.v1 import router as v1_router

# Configurar logging al inicio
setup_logging()
logger = get_logger(__name__)

# Validar configuración
settings.validate_configuration()

# Crear instancia de FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Microservicio RESTful para búsqueda semántica sobre catálogos de datos estructurados",
    docs_url="/docs",
    openapi_url="/openapi.json",
    contact={
        "name": "API de Búsqueda Semántica MENU",
        "url": "https://github.com/menu-api",
    },
    license_info={
        "name": "MIT",
    },
)

# Configurar esquema de seguridad para Swagger
from fastapi.openapi.utils import get_openapi
from fastapi.security import APIKeyHeader

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        description="Microservicio RESTful para búsqueda semántica sobre catálogos de datos estructurados",
        routes=app.routes,
    )
    
    # Agregar esquema de seguridad para API Key
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "Ingresa tu API Key aquí. Para pruebas usa: test_api_key_123"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"]
)

# Registrar routers de API
app.include_router(v1_router.router, prefix="/api")

# Preparar estructura para futuras versiones
# app.include_router(v2_router.router, prefix="/api")  # Futuro v2


@app.middleware("http")
async def security_and_logging_middleware(request: Request, call_next):
    """Middleware combinado para seguridad y logging."""
    start_time = time.time()
    client_ip = get_client_ip(request)
    
    # Validaciones de seguridad
    try:
        # Validar tamaño de petición
        content_length = request.headers.get("content-length")
        validate_request_size(content_length)
        
        # Log de petición entrante
        logger.info(
            "Petición entrante",
            method=request.method,
            url=str(request.url),
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent"),
            content_length=content_length
        )
        
        # Procesar petición
        response = await call_next(request)
        
        # Añadir headers de seguridad
        security_headers = SecurityHeaders.get_security_headers()
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Calcular tiempo de procesamiento
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        
        # Log de respuesta
        logger.info(
            "Petición completada",
            method=request.method,
            url=str(request.url),
            client_ip=client_ip,
            status_code=response.status_code,
            process_time=round(process_time, 4)
        )
        
        return response
        
    except HTTPException as e:
        # Log de error de validación
        logger.warning(
            "Error de validación en middleware",
            method=request.method,
            url=str(request.url),
            client_ip=client_ip,
            error=str(e.detail),
            status_code=e.status_code
        )
        raise e
    except Exception as e:
        # Log de error inesperado
        logger.error(
            "Error inesperado en middleware",
            method=request.method,
            url=str(request.url),
            client_ip=client_ip,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """Manejador específico para errores de autenticación."""
    client_ip = get_client_ip(request)
    logger.warning(
        "Error de autenticación",
        error_code=exc.error_code,
        message=exc.message,
        client_ip=client_ip,
        path=str(request.url.path),
        user_agent=request.headers.get("user-agent")
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            **exc.to_dict(),
            "path": str(request.url.path)
        },
        headers={"WWW-Authenticate": "ApiKey"}
    )


@app.exception_handler(AuthorizationError)
async def authorization_exception_handler(request: Request, exc: AuthorizationError):
    """Manejador específico para errores de autorización."""
    client_ip = get_client_ip(request)
    logger.warning(
        "Error de autorización",
        error_code=exc.error_code,
        message=exc.message,
        client_ip=client_ip,
        path=str(request.url.path),
        user_agent=request.headers.get("user-agent")
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            **exc.to_dict(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(MenuAPIException)
async def menu_exception_handler(request: Request, exc: MenuAPIException):
    """Manejador de excepciones personalizadas."""
    client_ip = get_client_ip(request)
    logger.error(
        "Error de aplicación",
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        client_ip=client_ip,
        path=str(request.url.path),
        details=exc.details
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            **exc.to_dict(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Manejador para excepciones HTTP de FastAPI."""
    client_ip = get_client_ip(request)
    logger.warning(
        "Error HTTP",
        status_code=exc.status_code,
        detail=exc.detail,
        client_ip=client_ip,
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "timestamp": time.time(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Manejador de excepciones generales."""
    client_ip = get_client_ip(request)
    logger.error(
        "Error interno del servidor",
        error=str(exc),
        error_type=type(exc).__name__,
        client_ip=client_ip,
        path=str(request.url.path),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "Error interno del servidor",
            "timestamp": time.time(),
            "path": str(request.url.path)
        }
    )


@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación."""
    logger.info(
        "Iniciando aplicación",
        app_name=settings.app_name,
        version=settings.app_version,
        log_level=settings.log_level,
        host=settings.host,
        port=settings.port
    )
    
    # Realizar warm-up automático de servicios
    try:
        logger.info("Iniciando warm-up automático de servicios")
        
        # 1. Inicializar y validar conexión a Qdrant
        try:
            logger.info("Inicializando conexión a Qdrant")
            from app.services.qdrant_service import get_qdrant_service
            
            qdrant_service = get_qdrant_service()
            
            # Validar conexión con health check
            qdrant_health = qdrant_service.health_check()
            
            if qdrant_health.get("status") == "healthy":
                logger.info(
                    "Conexión a Qdrant establecida exitosamente",
                    url=qdrant_health.get("url"),
                    collection=qdrant_health.get("collection_name"),
                    collection_exists=qdrant_health.get("collection_exists"),
                    total_collections=qdrant_health.get("total_collections")
                )
                
                # Asegurar que la colección existe
                if not qdrant_health.get("collection_exists"):
                    logger.info("Creando colección en Qdrant")
                    qdrant_service.ensure_collection(vector_size=1536)
                    logger.info("Colección creada exitosamente")
                else:
                    collection_info = qdrant_health.get("collection_info", {})
                    logger.info(
                        "Colección existente encontrada",
                        points_count=collection_info.get("points_count", 0),
                        vectors_count=collection_info.get("vectors_count", 0)
                    )
            else:
                logger.warning(
                    "Conexión a Qdrant no disponible",
                    status=qdrant_health.get("status"),
                    error=qdrant_health.get("error")
                )
                logger.warning("La aplicación continuará pero las operaciones de búsqueda pueden fallar")
                
        except Exception as e:
            logger.error(
                "Error inicializando Qdrant",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            logger.warning("La aplicación continuará pero las operaciones de búsqueda pueden fallar")
        
        # 2. Warm-up del servicio de embeddings
        try:
            logger.info("Iniciando warm-up de servicio de embeddings")
            from app.services.embedding_service import get_embedding_service
            
            embedding_service = get_embedding_service()
            warmup_result = await embedding_service.warmup()
            
            if warmup_result["status"] == "completed":
                logger.info(
                    "Warm-up de embeddings completado",
                    duration=f"{warmup_result['duration']:.3f}s",
                    queries_processed=warmup_result["queries_processed"]
                )
            else:
                logger.warning(
                    "Warm-up de embeddings falló",
                    error=warmup_result.get("error", "Unknown error")
                )
        except Exception as e:
            logger.error(
                "Error en warm-up de embeddings",
                error=str(e),
                error_type=type(e).__name__
            )
        
        # 3. Warm-up del servicio de búsqueda (opcional)
        try:
            logger.info("Realizando warm-up de búsqueda vectorial")
            from app.services.search_service import get_search_service
            
            search_service = get_search_service()
            
            # Realizar una búsqueda de prueba para inicializar el servicio
            test_results = await search_service.search("test warmup", top_k=1)
            logger.info(
                "Warm-up de búsqueda completado",
                results_found=len(test_results)
            )
        except Exception as e:
            logger.warning(
                "Warm-up de búsqueda falló",
                error=str(e),
                error_type=type(e).__name__
            )
            logger.warning("La aplicación continuará pero puede haber latencia en la primera búsqueda")
        
        logger.info("Warm-up automático completado exitosamente")
        
    except Exception as e:
        logger.error(
            "Error durante warm-up automático",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        # No fallar el startup por errores de warm-up
        logger.warning("Continuando startup sin warm-up completo")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre de la aplicación."""
    logger.info("Cerrando aplicación")


# Endpoints básicos (públicos)
@app.get("/", tags=["General"])
async def root():
    """
    Endpoint raíz de la API.
    
    Proporciona información básica sobre la API y enlaces
    a la documentación y endpoints principales.
    """
    logger.info("Acceso al endpoint raíz")
    return {
        "message": "API de Búsqueda Semántica MENU",
        "version": settings.app_version,
        "status": "running",
        "api_versions": {
            "v1": "/api/v1",
            "current": "v1"
        },
        "documentation": "/docs",
        "openapi": "/openapi.json",
        "endpoints": {
            "search": "/api/v1/buscar",
            "upsert": "/api/v1/consultas/upsert",
            "delete": "/api/v1/consultas/{query_id}",
            "health": "/api/v1/health",
            "info": "/api/v1/info"
        }
    }


@app.get("/health", tags=["General"])
async def health_check_basic():
    """
    Health check básico de la aplicación.
    
    Endpoint público para verificación rápida del estado
    del servicio sin detalles de dependencias.
    """
    logger.info("Health check básico solicitado")
    
    try:
        # Verificar estado de Qdrant
        from app.services.qdrant_service import get_qdrant_service
        qdrant_service = get_qdrant_service()
        qdrant_health = qdrant_service.health_check()
        
        # Determinar estado general
        overall_status = "healthy"
        if qdrant_health.get("status") != "healthy":
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "version": settings.app_version,
            "timestamp": time.time(),
            "services": {
                "qdrant": qdrant_health.get("status", "unknown")
            },
            "detailed_health": "/api/v1/health"
        }
    except Exception as e:
        logger.warning(f"Error en health check básico: {e}")
        return {
            "status": "degraded",
            "version": settings.app_version,
            "timestamp": time.time(),
            "detailed_health": "/api/v1/health"
        }


@app.get("/versions", tags=["General"])
async def api_versions():
    """
    Información sobre versiones disponibles de la API.
    
    Lista todas las versiones de API disponibles y sus
    características principales.
    """
    logger.info("Información de versiones solicitada")
    return {
        "current_version": "v1",
        "available_versions": {
            "v1": {
                "status": "stable",
                "base_path": "/api/v1",
                "features": [
                    "Búsqueda semántica con Qdrant",
                    "Sincronización de consultas guardadas (CRUD)",
                    "Health checks detallados",
                    "Autenticación por API Key"
                ],
                "endpoints": {
                    "search": "/api/v1/buscar",
                    "upsert": "/api/v1/consultas/upsert",
                    "delete": "/api/v1/consultas/{query_id}",
                    "health": "/api/v1/health",
                    "info": "/api/v1/info"
                }
            }
        },
        "deprecation_policy": "Las versiones se mantienen por al menos 6 meses después de deprecación",
        "migration_guide": "/docs#migration"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )