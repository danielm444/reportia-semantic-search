"""
Módulo de seguridad para autenticación y autorización.
Implementa autenticación por API Key usando FastAPI dependencies.
"""

from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader
from typing import Optional
from app.config.settings import settings
from app.core.logging import get_logger
from app.core.exceptions import AuthenticationError, AuthorizationError

logger = get_logger(__name__)

# Configurar esquemas de seguridad
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Dependency para validar API Key desde header X-API-Key.
    
    Args:
        api_key: Clave API desde header X-API-Key
        
    Returns:
        str: Clave API validada
        
    Raises:
        AuthenticationError: Si no se proporciona clave API
        AuthorizationError: Si la clave API es inválida
    """
    if not api_key:
        logger.warning("Intento de acceso sin API Key")
        raise AuthenticationError("Header X-API-Key requerido")
    
    if api_key != settings.menu_api_key:
        logger.warning(
            "Intento de acceso con API Key inválida",
            provided_key_prefix=api_key[:8] + "..." if len(api_key) > 8 else api_key
        )
        raise AuthorizationError("Clave API inválida")
    
    logger.debug("API Key validada exitosamente")
    return api_key


async def get_optional_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """
    Dependency opcional para validar API Key.
    No falla si no se proporciona, útil para endpoints públicos con funcionalidad extendida.
    
    Args:
        api_key: Clave API desde header X-API-Key
        
    Returns:
        Optional[str]: Clave API validada o None
    """
    if not api_key:
        return None
    
    if api_key != settings.menu_api_key:
        logger.warning(
            "API Key inválida en endpoint opcional",
            provided_key_prefix=api_key[:8] + "..." if len(api_key) > 8 else api_key
        )
        return None
    
    logger.debug("API Key opcional validada exitosamente")
    return api_key


def require_api_key(api_key: str = Depends(api_key_header)) -> str:
    """
    Dependency que requiere API Key válida.
    Usar en endpoints que requieren autenticación.
    
    Args:
        api_key: Clave API desde header
        
    Returns:
        str: Clave API validada
        
    Raises:
        HTTPException: Si la clave API es inválida
    """
    if api_key != settings.menu_api_key:
        logger.warning(
            "Intento de acceso con API Key inválida",
            provided_key_prefix=api_key[:8] + "..." if len(api_key) > 8 else api_key
        )
        raise HTTPException(
            status_code=403,
            detail="Clave API inválida"
        )
    
    logger.debug("API Key validada exitosamente")
    return api_key


def optional_api_key(api_key: Optional[str] = Depends(get_optional_api_key)) -> Optional[str]:
    """
    Dependency que permite API Key opcional.
    Usar en endpoints públicos con funcionalidad extendida para usuarios autenticados.
    
    Args:
        api_key: Clave API validada o None
        
    Returns:
        Optional[str]: Clave API validada o None
    """
    return api_key


class SecurityHeaders:
    """Clase para manejar headers de seguridad."""
    
    @staticmethod
    def get_security_headers() -> dict:
        """
        Retorna headers de seguridad recomendados.
        
        Returns:
            dict: Headers de seguridad
        """
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "font-src 'self' data:; "
                "connect-src 'self'"
            ),
        }


def validate_request_size(content_length: Optional[str]) -> None:
    """
    Valida el tamaño de la petición para prevenir ataques DoS.
    
    Args:
        content_length: Header Content-Length
        
    Raises:
        HTTPException: Si la petición es demasiado grande
    """
    if content_length:
        try:
            size = int(content_length)
            max_size = 1024 * 1024  # 1MB
            if size > max_size:
                logger.warning(f"Petición demasiado grande: {size} bytes")
                raise HTTPException(
                    status_code=413,
                    detail="Petición demasiado grande"
                )
        except ValueError:
            logger.warning(f"Content-Length inválido: {content_length}")


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitiza entrada de texto para prevenir ataques.
    
    Args:
        text: Texto a sanitizar
        max_length: Longitud máxima permitida
        
    Returns:
        str: Texto sanitizado
        
    Raises:
        HTTPException: Si el texto es demasiado largo
    """
    if len(text) > max_length:
        logger.warning(f"Texto demasiado largo: {len(text)} caracteres")
        raise HTTPException(
            status_code=400,
            detail=f"Texto demasiado largo. Máximo {max_length} caracteres."
        )
    
    # Remover caracteres de control peligrosos
    sanitized = text.replace('\x00', '').replace('\r', '').replace('\n', ' ')
    
    # Limitar caracteres especiales consecutivos
    import re
    sanitized = re.sub(r'[<>]{2,}', '', sanitized)
    
    return sanitized.strip()


def get_client_ip(request) -> str:
    """
    Obtiene la IP real del cliente considerando proxies.
    
    Args:
        request: Objeto Request de FastAPI
        
    Returns:
        str: IP del cliente
    """
    # Verificar headers de proxy comunes
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Tomar la primera IP (cliente original)
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback a la IP directa
    return request.client.host if request.client else "unknown"