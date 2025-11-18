"""
Modelos de datos compartidos para el sistema de búsqueda.
Define estructuras de datos internas y de dominio.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
from app.core.text_normalizer import normalize_text


class DocumentStatus(str, Enum):
    """Estados posibles de un documento."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    DELETED = "deleted"


class MenuItemType(str, Enum):
    """Tipos de elementos del menú."""
    CONFIGURATION = "configuration"
    REPORT = "report"
    USER_MANAGEMENT = "user_management"
    HELP = "help"
    OTHER = "other"
    # Nuevos tipos encontrados en los datos
    APPOINTMENTS = "appointments"
    MANAGEMENT = "management"
    BACKEND = "backend"
    TOOLS = "tools"
    SECURITY = "security"


class MenuItem(BaseModel):
    """Modelo para elementos del menú del sistema."""
    
    ID: int = Field(
        ...,
        description="Identificador único del elemento",
        ge=1
    )
    
    Nivel0: str = Field(
        ...,
        description="Categoría principal",
        min_length=1,
        max_length=100
    )
    
    Nivel1: Optional[str] = Field(
        None,
        description="Subcategoría",
        max_length=100
    )
    
    Descripcion: str = Field(
        ...,
        description="Descripción del elemento",
        min_length=1,
        max_length=500
    )
    
    url: str = Field(
        ...,
        description="URL del elemento",
        min_length=1,
        max_length=200
    )
    
    # Campos adicionales opcionales
    keywords: Optional[List[str]] = Field(
        None,
        description="Palabras clave para búsqueda"
    )
    
    item_type: Optional[MenuItemType] = Field(
        None,
        description="Tipo de elemento del menú"
    )
    
    status: DocumentStatus = Field(
        default=DocumentStatus.ACTIVE,
        description="Estado del documento"
    )
    
    created_at: Optional[datetime] = Field(
        None,
        description="Fecha de creación"
    )
    
    updated_at: Optional[datetime] = Field(
        None,
        description="Fecha de última actualización"
    )
    
    # NUEVOS CAMPOS para formato JSON optimizado
    sinonimos: Optional[List[str]] = Field(
        None,
        description="Sinónimos para mejorar búsqueda semántica"
    )
    
    acciones: Optional[List[str]] = Field(
        None,
        description="Acciones/verbos relacionados con el elemento"
    )
    
    texto_indexado: Optional[str] = Field(
        None,
        description="Texto pre-calculado para indexación (opcional)"
    )
    
    # Campos alternativos para formato JSON extendido (compatibilidad)
    id: Optional[int] = Field(
        None,
        description="ID alternativo (formato extendido)"
    )
    
    titulo: Optional[str] = Field(
        None,
        description="Título alternativo (formato extendido)"
    )
    
    nivel: Optional[List[str]] = Field(
        None,
        description="Niveles como array (formato extendido)"
    )
    
    descripcion: Optional[str] = Field(
        None,
        description="Descripción alternativa (formato extendido)"
    )
    
    idioma: Optional[str] = Field(
        None,
        description="Idioma del elemento"
    )
    
    estado: Optional[str] = Field(
        None,
        description="Estado alternativo (formato extendido)"
    )
    
    tipo: Optional[str] = Field(
        None,
        description="Tipo alternativo (formato extendido)"
    )
    
    @field_validator('Nivel0', 'Nivel1', 'Descripcion')
    @classmethod
    def validate_text_fields(cls, v):
        """Valida que los campos de texto no estén vacíos después de strip."""
        if v and not v.strip():
            raise ValueError('Los campos de texto no pueden estar vacíos')
        return v.strip() if v else v
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        """Valida formato básico de URL."""
        if not v.strip():
            raise ValueError('La URL no puede estar vacía')
        # Validación básica - puede expandirse
        return v.strip()
    
    def to_search_text(self) -> str:
        """
        Genera texto canónico optimizado para búsqueda semántica.
        Soporta formato actual y extendido. Usa texto_indexado si está presente.
        
        Returns:
            str: Texto canónico normalizado (sin tildes, minúsculas)
        """
        # Si hay texto_indexado pre-calculado, usarlo directamente
        if self.texto_indexado:
            return normalize_text(self.texto_indexado)
        
        # Determinar campos a usar (formato actual vs extendido)
        nivel0 = self.Nivel0
        nivel1 = self.Nivel1
        descripcion = self.Descripcion
        
        # Soporte para formato extendido
        if self.nivel and len(self.nivel) > 0:
            nivel0 = self.nivel[0]
            nivel1 = self.nivel[1] if len(self.nivel) > 1 else None
        
        if self.descripcion:
            descripcion = self.descripcion
        
        # Construir ruta del menú
        ruta = f"Ruta del menú: {nivel0}"
        if nivel1:
            ruta += f" > {nivel1}"
        
        # Construir texto base con formato canónico
        partes = [
            f"{ruta}.",
            f"Descripción: {descripcion}."
        ]
        
        # Agregar términos adicionales
        terminos_extra = []
        
        # Keywords existentes
        if self.keywords:
            terminos_extra.extend(self.keywords)
        
        # NUEVO: Sinónimos del formato extendido
        if self.sinonimos:
            terminos_extra.extend(self.sinonimos)
        
        # NUEVO: Acciones del formato extendido
        if self.acciones:
            terminos_extra.extend(self.acciones)
        
        # Deduplicar términos extra
        if terminos_extra:
            terminos_unicos = []
            for termino in terminos_extra:
                if termino and termino.strip() and termino not in terminos_unicos:
                    terminos_unicos.append(termino)
            
            if terminos_unicos:
                partes.extend(terminos_unicos)
        
        # Unir todas las partes
        texto_base = " ".join(partes)
        
        # Aplicar normalización (quitar tildes, minúsculas, trim)
        return normalize_text(texto_base)
    
    def get_effective_id(self) -> int:
        """Obtiene el ID efectivo (formato actual o extendido)."""
        return self.id if self.id is not None else self.ID
    
    def get_effective_description(self) -> str:
        """Obtiene la descripción efectiva (formato actual o extendido)."""
        return self.descripcion if self.descripcion else self.Descripcion
    
    def get_effective_status(self) -> str:
        """Obtiene el estado efectivo (formato actual o extendido)."""
        if self.estado:
            return self.estado
        return self.status.value if self.status else "active"
    
    def is_extended_format(self) -> bool:
        """Verifica si el elemento usa formato extendido."""
        return any([
            self.id is not None,
            self.titulo is not None,
            self.nivel is not None,
            self.descripcion is not None,
            self.sinonimos is not None,
            self.acciones is not None,
            self.texto_indexado is not None
        ])
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el modelo a diccionario para almacenamiento.
        
        Returns:
            Dict[str, Any]: Representación en diccionario
        """
        return self.dict(exclude_none=True)
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "examples": [
                {
                    "ID": 2,
                    "Nivel0": "Configuración",
                    "Nivel1": "Alertas",
                    "Descripcion": "Configura las notificaciones y alertas del sistema",
                    "url": "localhost/config/alertas",
                    "keywords": ["notificaciones", "alertas", "configuración"],
                    "item_type": "configuration",
                    "status": "active"
                },
                {
                    "id": 3,
                    "titulo": "Usuarios › Gestión",
                    "nivel": ["Usuarios", "Gestión"],
                    "descripcion": "Administrar usuarios y permisos del sistema",
                    "sinonimos": ["personas", "colaboradores", "roles", "permisos", "cuentas"],
                    "acciones": ["crear", "administrar", "invitar", "asignar permisos", "gestionar"],
                    "texto_indexado": "Usuarios › Gestión. Administrar usuarios y permisos del sistema.",
                    "url": "localhost/usuarios/gestion",
                    "idioma": "es",
                    "estado": "active",
                    "tipo": "item"
                }
            ]
        }


class SearchQuery(BaseModel):
    """Modelo interno para consultas de búsqueda."""
    
    text: str = Field(
        ...,
        description="Texto de la consulta",
        min_length=1,
        max_length=1000
    )
    
    limit: int = Field(
        default=3,
        description="Número máximo de resultados",
        ge=1,
        le=50
    )
    
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Filtros adicionales para la búsqueda"
    )
    
    include_inactive: bool = Field(
        default=False,
        description="Incluir elementos inactivos en la búsqueda"
    )
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        """Valida que el texto no esté vacío después de strip."""
        if not v.strip():
            raise ValueError('El texto de consulta no puede estar vacío')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "configurar alertas del sistema",
                "limit": 5,
                "filters": {"Nivel0": "Configuración"},
                "include_inactive": False
            }
        }


class SearchResultItem(BaseModel):
    """Modelo interno para resultados de búsqueda."""
    
    document: MenuItem = Field(
        ...,
        description="Documento encontrado"
    )
    
    score: float = Field(
        ...,
        description="Puntuación de relevancia",
        ge=0.0,
        le=1.0
    )
    
    matched_fields: Optional[List[str]] = Field(
        None,
        description="Campos que coincidieron con la búsqueda"
    )
    
    highlights: Optional[Dict[str, str]] = Field(
        None,
        description="Fragmentos destacados del texto"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "document": {
                    "ID": 2,
                    "Nivel0": "Configuración",
                    "Nivel1": "Alertas",
                    "Descripcion": "Configura las notificaciones y alertas del sistema",
                    "url": "localhost/config/alertas"
                },
                "score": 0.85,
                "matched_fields": ["Descripcion", "Nivel1"],
                "highlights": {
                    "Descripcion": "Configura las <em>notificaciones</em> y <em>alertas</em>"
                }
            }
        }


class IndexingJob(BaseModel):
    """Modelo para trabajos de indexación."""
    
    job_id: str = Field(
        ...,
        description="Identificador único del trabajo"
    )
    
    status: str = Field(
        ...,
        description="Estado del trabajo",
        pattern="^(pending|running|completed|failed)$"
    )
    
    source_file: str = Field(
        ...,
        description="Archivo fuente para indexación"
    )
    
    documents_total: Optional[int] = Field(
        None,
        description="Total de documentos a procesar",
        ge=0
    )
    
    documents_processed: int = Field(
        default=0,
        description="Documentos procesados",
        ge=0
    )
    
    started_at: Optional[datetime] = Field(
        None,
        description="Fecha de inicio del trabajo"
    )
    
    completed_at: Optional[datetime] = Field(
        None,
        description="Fecha de finalización del trabajo"
    )
    
    error_message: Optional[str] = Field(
        None,
        description="Mensaje de error si el trabajo falló"
    )
    
    processing_time: Optional[float] = Field(
        None,
        description="Tiempo de procesamiento en segundos",
        ge=0.0
    )
    
    @field_validator('documents_processed')
    @classmethod
    def validate_processed_count(cls, v, values):
        """Valida que los documentos procesados no excedan el total."""
        total = values.get('documents_total')
        if total is not None and v > total:
            raise ValueError('Los documentos procesados no pueden exceder el total')
        return v
    
    def get_progress_percentage(self) -> Optional[float]:
        """
        Calcula el porcentaje de progreso.
        
        Returns:
            Optional[float]: Porcentaje de progreso (0-100)
        """
        if self.documents_total and self.documents_total > 0:
            return (self.documents_processed / self.documents_total) * 100
        return None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "idx_20240101_120000",
                "status": "running",
                "source_file": "data/menu.json",
                "documents_total": 100,
                "documents_processed": 45,
                "started_at": "2024-01-01T12:00:00Z",
                "processing_time": 15.5
            }
        }


class EmbeddingVector(BaseModel):
    """Modelo para vectores de embedding."""
    
    document_id: Union[str, int] = Field(
        ...,
        description="ID del documento asociado"
    )
    
    vector: List[float] = Field(
        ...,
        description="Vector de embedding",
        min_items=1
    )
    
    dimension: int = Field(
        ...,
        description="Dimensión del vector",
        ge=1
    )
    
    model_name: str = Field(
        ...,
        description="Nombre del modelo usado para generar el embedding"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha de creación del embedding"
    )
    
    @field_validator('dimension')
    @classmethod
    def validate_dimension_matches_vector(cls, v, values):
        """Valida que la dimensión coincida con la longitud del vector."""
        vector = values.get('vector')
        if vector and len(vector) != v:
            raise ValueError('La dimensión debe coincidir con la longitud del vector')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_123",
                "vector": [0.1, 0.2, 0.3, -0.1, 0.5],
                "dimension": 5,
                "model_name": "text-embedding-3-small",
                "created_at": "2024-01-01T12:00:00Z"
            }
        }