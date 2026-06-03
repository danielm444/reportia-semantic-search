"""Tests del normalizador de texto."""

from app.core.text_normalizer import (
    quitar_tildes,
    normalize_text,
    normalize_query,
    validate_normalized_text,
)


def test_quitar_tildes():
    assert quitar_tildes("Configuración") == "Configuracion"
    assert quitar_tildes("notificación") == "notificacion"
    assert quitar_tildes("ñoño") == "nono"
    assert quitar_tildes("") == ""


def test_normalize_text_lower_trim_spaces():
    assert normalize_text("  Configuración del SISTEMA  ") == "configuracion del sistema"
    assert normalize_text("Múltiples   espacios") == "multiples espacios"
    assert normalize_text(None) == ""


def test_normalize_query_matches_normalize_text():
    assert normalize_query("¿Dónde configuro las ALERTAS?") == "¿donde configuro las alertas?"
    # Consulta e indexación normalizan igual (consistencia)
    assert normalize_query("Configuración") == normalize_text("Configuración")


def test_validate_normalized_text():
    assert validate_normalized_text("configuracion del sistema") is True
    assert validate_normalized_text("Configuración") is False
    assert validate_normalized_text("hola  mundo") is False
