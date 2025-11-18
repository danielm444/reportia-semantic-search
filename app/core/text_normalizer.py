"""
Módulo de normalización de texto para optimización de búsqueda semántica.
Proporciona funciones para normalizar texto de forma consistente entre indexación y consultas.
"""

import unicodedata
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)


def quitar_tildes(texto: str) -> str:
    """
    Elimina tildes y acentos usando normalización Unicode NFD.
    
    Args:
        texto: Texto con posibles tildes y acentos
        
    Returns:
        str: Texto sin tildes ni acentos
        
    Examples:
        >>> quitar_tildes("Configuración")
        'Configuracion'
        >>> quitar_tildes("notificación")
        'notificacion'
        >>> quitar_tildes("ñoño")
        'nono'
    """
    if not texto:
        return ""
    
    try:
        # Normalizar a NFD (descomponer caracteres acentuados)
        normalized = unicodedata.normalize('NFD', texto)
        
        # Filtrar marcas diacríticas (categoría Mn - Nonspacing_Mark)
        sin_tildes = ''.join(
            char for char in normalized 
            if unicodedata.category(char) != 'Mn'
        )
        
        return sin_tildes
        
    except Exception as e:
        logger.warning(f"Error eliminando tildes del texto '{texto[:50]}...': {e}")
        return texto  # Retornar texto original si falla


def normalize_text(texto: str) -> str:
    """
    Normalización completa de texto: quita tildes, convierte a minúsculas y elimina espacios extra.
    
    Args:
        texto: Texto a normalizar
        
    Returns:
        str: Texto normalizado (sin tildes, minúsculas, sin espacios extra)
        
    Examples:
        >>> normalize_text("  Configuración del SISTEMA  ")
        'configuracion del sistema'
        >>> normalize_text("Notificación")
        'notificacion'
        >>> normalize_text("")
        ''
        >>> normalize_text(None)
        ''
    """
    if not texto:
        return ""
    
    try:
        # Aplicar transformaciones en orden
        normalizado = quitar_tildes(texto)
        normalizado = normalizado.lower()
        normalizado = normalizado.strip()
        
        # Normalizar espacios múltiples a uno solo
        normalizado = ' '.join(normalizado.split())
        
        return normalizado
        
    except Exception as e:
        logger.warning(f"Error normalizando texto '{texto[:50]}...': {e}")
        return texto.lower().strip() if texto else ""


def normalize_query(consulta: str) -> str:
    """
    Normaliza una consulta de búsqueda aplicando las mismas reglas que el texto indexado.
    
    Args:
        consulta: Consulta de búsqueda del usuario
        
    Returns:
        str: Consulta normalizada
        
    Examples:
        >>> normalize_query("¿Dónde configuro las ALERTAS?")
        'donde configuro las alertas'
        >>> normalize_query("  Configuración de usuarios  ")
        'configuracion de usuarios'
    """
    if not consulta or not consulta.strip():
        return ""
    
    # Usar la misma normalización que el texto indexado
    return normalize_text(consulta)


def validate_normalized_text(texto: str) -> bool:
    """
    Valida que un texto esté correctamente normalizado.
    
    Args:
        texto: Texto a validar
        
    Returns:
        bool: True si el texto está normalizado, False en caso contrario
    """
    if not texto:
        return True  # Texto vacío se considera válido
    
    # Verificar que no tenga tildes
    sin_tildes = quitar_tildes(texto)
    if sin_tildes != texto:
        return False
    
    # Verificar que esté en minúsculas
    if texto != texto.lower():
        return False
    
    # Verificar que no tenga espacios extra al inicio/final
    if texto != texto.strip():
        return False
    
    # Verificar que no tenga espacios múltiples
    if '  ' in texto:
        return False
    
    return True


# Funciones de utilidad para debugging y testing
def compare_normalization(texto1: str, texto2: str) -> dict:
    """
    Compara la normalización de dos textos y retorna información detallada.
    Útil para debugging y testing.
    
    Args:
        texto1: Primer texto
        texto2: Segundo texto
        
    Returns:
        dict: Información de comparación
    """
    norm1 = normalize_text(texto1)
    norm2 = normalize_text(texto2)
    
    return {
        "texto1_original": texto1,
        "texto2_original": texto2,
        "texto1_normalizado": norm1,
        "texto2_normalizado": norm2,
        "son_equivalentes": norm1 == norm2,
        "longitud_original": (len(texto1 or ""), len(texto2 or "")),
        "longitud_normalizada": (len(norm1), len(norm2))
    }


def get_normalization_stats(textos: list) -> dict:
    """
    Obtiene estadísticas de normalización para una lista de textos.
    
    Args:
        textos: Lista de textos a analizar
        
    Returns:
        dict: Estadísticas de normalización
    """
    if not textos:
        return {"error": "Lista de textos vacía"}
    
    stats = {
        "total_textos": len(textos),
        "textos_con_tildes": 0,
        "textos_con_mayusculas": 0,
        "textos_con_espacios_extra": 0,
        "longitud_promedio_original": 0,
        "longitud_promedio_normalizada": 0,
        "reduccion_promedio_longitud": 0
    }
    
    longitudes_originales = []
    longitudes_normalizadas = []
    
    for texto in textos:
        if not texto:
            continue
            
        normalizado = normalize_text(texto)
        
        # Contar características
        if quitar_tildes(texto) != texto:
            stats["textos_con_tildes"] += 1
        
        if texto != texto.lower():
            stats["textos_con_mayusculas"] += 1
        
        if texto != texto.strip() or '  ' in texto:
            stats["textos_con_espacios_extra"] += 1
        
        # Calcular longitudes
        longitudes_originales.append(len(texto))
        longitudes_normalizadas.append(len(normalizado))
    
    # Calcular promedios
    if longitudes_originales:
        stats["longitud_promedio_original"] = sum(longitudes_originales) / len(longitudes_originales)
        stats["longitud_promedio_normalizada"] = sum(longitudes_normalizadas) / len(longitudes_normalizadas)
        stats["reduccion_promedio_longitud"] = stats["longitud_promedio_original"] - stats["longitud_promedio_normalizada"]
    
    return stats