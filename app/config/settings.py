"""
Configuración del sistema MENU usando Pydantic Settings.
Carga todas las variables desde archivo .env.
"""

from pydantic import Field, validator
from pydantic_settings import BaseSettings
from typing import List
import os
import logging


class Settings(BaseSettings):
    """Configuración principal del sistema MENU."""
    
    # API Configuration
    menu_api_key: str = Field(..., env="MENU_API_KEY", description="Clave API para autenticación")
    cors_allowed_origins: str = Field(
        default="http://localhost:4000", 
        env="CORS_ALLOWED_ORIGINS", 
        description="Orígenes permitidos para CORS (separados por comas)"
    )
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY", description="Clave API de OpenAI")
    openai_timeout: float = Field(default=10.0, env="OPENAI_TIMEOUT", description="Timeout para requests a OpenAI (segundos)")
    openai_max_retries: int = Field(default=2, env="OPENAI_MAX_RETRIES", description="Máximo número de reintentos para OpenAI")
    openai_max_concurrent: int = Field(default=5, env="OPENAI_MAX_CONCURRENT", description="Máximo requests concurrentes a OpenAI")
    
    # LangChain Configuration (Optional)
    langchain_api_key: str = Field(default="", env="LANGCHAIN_API_KEY", description="Clave API de LangChain (opcional)")
    
    # Database Configuration (ChromaDB - DEPRECATED - usar Qdrant)
    chroma_db_path: str = Field(
        default="./data/chroma_db", 
        env="CHROMA_DB_PATH", 
        description="[DEPRECATED] Ruta para ChromaDB. Ya no se usa. Migrado a Qdrant."
    )
    
    # Qdrant Configuration
    qdrant_url: str = Field(
        default="http://localhost:6333",
        env="QDRANT_URL",
        description="URL de conexión a Qdrant"
    )
    qdrant_api_key: str = Field(
        default="",
        env="QDRANT_API_KEY",
        description="API Key de Qdrant (opcional para instancias locales)"
    )
    qdrant_collection_name: str = Field(
        default="saved_queries",
        env="QDRANT_COLLECTION_NAME",
        description="Nombre de la colección en Qdrant"
    )
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL", description="Nivel de logging")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST", description="Host del servidor")
    port: int = Field(default=8000, env="PORT", description="Puerto del servidor")
    
    # App metadata
    app_name: str = "Reportia Semantic Search API"
    app_version: str = "2.0.0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Valida que el nivel de log sea válido."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level debe ser uno de: {valid_levels}')
        return v.upper()
    
    @validator('port')
    def validate_port(cls, v):
        """Valida que el puerto esté en rango válido."""
        if not 1 <= v <= 65535:
            raise ValueError('port debe estar entre 1 y 65535')
        return v
    
    @validator('openai_api_key')
    def validate_openai_key(cls, v):
        """Valida formato básico de clave OpenAI."""
        if not v.startswith('sk-'):
            # Solo advertir en desarrollo, no fallar
            pass
        return v
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convierte la cadena de orígenes CORS en una lista."""
        return [origin.strip() for origin in self.cors_allowed_origins.split(",")]
    
    @property
    def log_level_int(self) -> int:
        """Retorna el nivel de log como entero."""
        return getattr(logging, self.log_level, logging.INFO)
    
    def ensure_chroma_db_directory(self) -> None:
        """
        [DEPRECATED] Asegura que el directorio de ChromaDB exista.
        Este método ya no se usa. La aplicación ahora usa Qdrant.
        """
        import warnings
        warnings.warn(
            "ensure_chroma_db_directory está deprecated. La aplicación usa Qdrant ahora.",
            DeprecationWarning,
            stacklevel=2
        )
        os.makedirs(self.chroma_db_path, exist_ok=True)
    
    def validate_configuration(self) -> None:
        """Valida la configuración completa del sistema."""
        # NOTA: Ya no creamos directorio de ChromaDB automáticamente
        # La aplicación ahora usa Qdrant como base de datos vectorial
        
        # Validar que las claves no sean valores de ejemplo
        if self.menu_api_key in ['tu_clave_secreta_aqui', 'test_api_key_123']:
            import warnings
            warnings.warn("Usando clave API de ejemplo. Cambiar en producción.")
        
        if 'placeholder' in self.openai_api_key.lower():
            import warnings
            warnings.warn("Usando clave OpenAI de ejemplo. Configurar clave real.")


# Instancia global de configuración
settings = Settings()