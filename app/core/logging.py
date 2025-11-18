"""
Configuración de logging estructurado en JSON para el sistema MENU.
Utiliza structlog para logs estructurados y configurables.
"""

import logging
import sys
from typing import Any, Dict
import structlog
from structlog.types import EventDict, Processor
from app.config.settings import settings


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Añade contexto de la aplicación a todos los logs."""
    event_dict["app"] = settings.app_name
    event_dict["version"] = settings.app_version
    return event_dict


def filter_sensitive_data(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Filtra datos sensibles de los logs."""
    # Lista de campos que no deben aparecer en logs
    sensitive_fields = ["api_key", "password", "token", "secret", "authorization"]
    
    for field in sensitive_fields:
        if field in event_dict:
            event_dict[field] = "***FILTERED***"
    
    # Filtrar headers de autorización
    if "headers" in event_dict and isinstance(event_dict["headers"], dict):
        headers = event_dict["headers"].copy()
        for key in headers:
            if key.lower() in ["authorization", "x-api-key"]:
                headers[key] = "***FILTERED***"
        event_dict["headers"] = headers
    
    return event_dict


def setup_logging() -> None:
    """
    Configura el sistema de logging estructurado.
    Debe llamarse al inicio de la aplicación.
    """
    # Configurar el nivel de logging desde configuración
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Configurar structlog
    structlog.configure(
        processors=[
            # Añadir contexto de aplicación
            add_app_context,
            # Filtrar datos sensibles
            filter_sensitive_data,
            # Añadir timestamp
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            # Procesar stack info si está disponible
            structlog.processors.StackInfoRenderer(),
            # Formatear excepciones
            structlog.processors.format_exc_info,
            # Renderizar como JSON
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configurar el logger estándar de Python
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Configurar loggers de terceros para evitar spam
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    Obtiene un logger estructurado.
    
    Args:
        name: Nombre del logger (opcional)
    
    Returns:
        Logger estructurado configurado
    """
    return structlog.get_logger(name)


# Logger principal para el módulo
logger = get_logger(__name__)