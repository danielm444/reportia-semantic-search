"""Tests del núcleo genérico de SearchService (con Qdrant en memoria)."""

import pytest

from app.core.exceptions import SearchError, QueryNotFoundError
from app.services.search_service import coerce_point_id


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

async def _seed(svc):
    """Indexa un set base de documentos para las pruebas."""
    docs = [
        {"id": 1, "texto": "seguridad usuarios cuentas", "payload": {"tipo": "security"}},
        {"id": 2, "texto": "gestion reportes turnos", "payload": {"tipo": "management"}},
        {"id": 3, "texto": "seguridad permisos roles", "payload": {"tipo": "security"}},
    ]
    await svc.upsert_documents(docs)


# --------------------------------------------------------------------------- #
# coerce_point_id
# --------------------------------------------------------------------------- #

def test_coerce_point_id_int_passthrough():
    assert coerce_point_id(42) == 42


def test_coerce_point_id_string_is_deterministic_uuid():
    a = coerce_point_id("menu-usuarios")
    b = coerce_point_id("menu-usuarios")
    assert a == b
    assert a != coerce_point_id("menu-otra")


# --------------------------------------------------------------------------- #
# Round-trip y búsqueda
# --------------------------------------------------------------------------- #

async def test_upsert_and_search_returns_full_payload(search_service):
    await _seed(search_service)
    results = await search_service.search("usuarios", top_k=3)

    assert results, "debe haber resultados"
    top = results[0]
    # El resultado top corresponde al doc con 'usuarios'
    assert top["data"]["id"] == 1
    assert top["data"]["tipo"] == "security"
    # Scores descendentes
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


async def test_search_respects_top_k(search_service):
    await _seed(search_service)
    results = await search_service.search("seguridad", top_k=1)
    assert len(results) == 1


async def test_filters_restrict_by_payload(search_service):
    await _seed(search_service)
    results = await search_service.search("seguridad", top_k=10, filters={"tipo": "management"})
    assert results
    assert all(r["data"]["tipo"] == "management" for r in results)


async def test_filters_with_list_value_or_semantics(search_service):
    await _seed(search_service)
    results = await search_service.search(
        "seguridad gestion", top_k=10, filters={"tipo": ["security", "management"]}
    )
    tipos = {r["data"]["tipo"] for r in results}
    assert tipos.issubset({"security", "management"})
    assert len(results) == 3


async def test_score_threshold_filters_low_scores(search_service):
    await _seed(search_service)
    # Umbral imposible → sin resultados
    results = await search_service.search("usuarios", top_k=10, score_threshold=0.999)
    assert results == [] or all(r["score"] >= 0.999 for r in results)


async def test_pagination_offset(search_service):
    await _seed(search_service)
    page1 = await search_service.search("seguridad", top_k=1, offset=0)
    page2 = await search_service.search("seguridad", top_k=1, offset=1)
    assert page1 and page2
    assert page1[0]["data"]["id"] != page2[0]["data"]["id"]


async def test_string_id_round_trip_and_delete(search_service):
    await search_service.upsert_document("menu-x", "texto unico zzz", {"tipo": "custom"})
    results = await search_service.search("zzz", top_k=1)
    assert results[0]["data"]["id"] == "menu-x"

    assert search_service.delete_document("menu-x") is True
    # Tras borrar, no aparece
    results = await search_service.search("zzz", top_k=5)
    assert all(r["data"].get("id") != "menu-x" for r in results)


# --------------------------------------------------------------------------- #
# Validaciones y adaptadores
# --------------------------------------------------------------------------- #

async def test_search_empty_query_raises(search_service):
    with pytest.raises(SearchError):
        await search_service.search("   ", top_k=3)


async def test_upsert_query_adapter_and_delete(search_service):
    query = {
        "id": 123,
        "name": "Reporte de ventas mensuales",
        "description": "Ventas por mes y region",
        "query_sql_original": "SELECT * FROM sales",
        "engine_code": "postgres",
        "company_id": 1,
        "owner_user_id": 1,
        "version": 1,
        "is_active": True,
    }
    result = await search_service.upsert_query(query)
    assert result["id"] == 123

    found = await search_service.search("ventas", top_k=1)
    assert found[0]["data"]["name"] == "Reporte de ventas mensuales"

    assert await search_service.delete_query(123) is True
    with pytest.raises(QueryNotFoundError):
        await search_service.delete_query(123)
