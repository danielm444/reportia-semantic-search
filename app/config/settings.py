"""
Configuración del sistema usando Pydantic Settings (Pydantic v2).
Carga todas las variables desde archivo .env. Los nombres de las variables de
entorno se derivan del nombre del campo (case-insensitive): p. ej. el campo
``menu_api_key`` se lee de ``MENU_API_KEY``.
"""

import os
import logging
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración principal del sistema."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Configuration
    menu_api_key: str = Field(..., description="Clave API para autenticación")
    cors_allowed_origins: str = Field(
        default="http://localhost:4000",
        description="Orígenes permitidos para CORS (separados por comas)",
    )

    # OpenAI Configuration
    openai_api_key: str = Field(..., description="Clave API de OpenAI")
    openai_timeout: float = Field(default=10.0, description="Timeout para requests a OpenAI (segundos)")
    openai_max_retries: int = Field(default=2, description="Máximo número de reintentos para OpenAI")
    openai_max_concurrent: int = Field(default=5, description="Máximo requests concurrentes a OpenAI")

    # LangChain Configuration (Optional)
    langchain_api_key: str = Field(default="", description="Clave API de LangChain (opcional)")

    # Database Configuration (ChromaDB - DEPRECATED - usar Qdrant)
    chroma_db_path: str = Field(
        default="./data/chroma_db",
        description="[DEPRECATED] Ruta para ChromaDB. Ya no se usa. Migrado a Qdrant.",
    )

    # Qdrant Configuration
    qdrant_url: str = Field(default="http://localhost:6333", description="URL de conexión a Qdrant")
    qdrant_api_key: str = Field(default="", description="API Key de Qdrant (opcional para instancias locales)")
    qdrant_collection_name: str = Field(default="saved_queries", description="Nombre de la colección en Qdrant")

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Nivel de logging")

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Host del servidor")
    port: int = Field(default=8000, description="Puerto del servidor")

    # App metadata
    app_name: str = "Reportia Semantic Search API"
    app_version: str = "2.0.0"

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Valida que el nivel de log sea válido."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level debe ser uno de: {valid_levels}')
        return v.upper()

    @field_validator('port')
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Valida que el puerto esté en rango válido."""
        if not 1 <= v <= 65535:
            raise ValueError('port debe estar entre 1 y 65535')
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        """Convierte la cadena de orígenes CORS en una lista."""
        return [origin.strip() for origin in self.cors_allowed_origins.split(",")]

    @property
    def log_level_int(self) -> int:
        """Retorna el nivel de log como entero."""
        return getattr(logging, self.log_level, logging.INFO)

    def validate_configuration(self) -> None:
        """Valida la configuración completa del sistema."""
        # La aplicación usa Qdrant como base de datos vectorial (no crea dir de ChromaDB).
        if self.menu_api_key in ['tu_clave_secreta_aqui', 'test_api_key_123']:
            import warnings
            warnings.warn("Usando clave API de ejemplo. Cambiar en producción.")

        if 'placeholder' in self.openai_api_key.lower():
            import warnings
            warnings.warn("Usando clave OpenAI de ejemplo. Configurar clave real.")


# Instancia global de configuración
settings = Settings()
