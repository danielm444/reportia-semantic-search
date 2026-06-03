"""Tests del modelo MenuItem (texto de búsqueda y getters efectivos)."""

from app.models.search_models import MenuItem


def _extended_item(**overrides):
    data = {
        "ID": 36,
        "Nivel0": "Seguridad",
        "Nivel1": "Usuarios",
        "Descripcion": "Gestionar usuarios del sistema y sus credenciales.",
        "url": "wwusersgam.aspx",
        "id": 36,
        "titulo": "Seguridad › Usuarios",
        "nivel": ["Seguridad", "Usuarios"],
        "descripcion": "Gestionar usuarios del sistema y sus credenciales.",
        "sinonimos": ["cuentas", "personas", "operadores"],
        "acciones": ["crear", "editar", "bloquear"],
        "estado": "active",
        "tipo": "security",
    }
    data.update(overrides)
    return MenuItem(**data)


def test_to_search_text_uses_texto_indexado_when_present():
    item = _extended_item(texto_indexado="Ruta del menú: Seguridad > Usuarios. Descripción: X.")
    text = item.to_search_text()
    assert "seguridad" in text
    assert "usuarios" in text
    # normalizado: sin tildes ni mayúsculas
    assert text == text.lower()


def test_to_search_text_builds_from_fields_and_includes_synonyms():
    item = _extended_item(texto_indexado=None)
    text = item.to_search_text()
    assert "seguridad" in text
    assert "usuarios" in text
    assert "cuentas" in text  # sinónimo
    assert "crear" in text    # acción


def test_get_effective_helpers():
    item = _extended_item()
    assert item.get_effective_id() == 36
    assert item.get_effective_status() == "active"
    assert "usuarios" in item.get_effective_description().lower()
    assert item.is_extended_format() is True
