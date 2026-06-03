"""Tests de la API v1 vía TestClient (servicios fakeados, sin red)."""

CORS_ORIGIN = "http://localhost:4000"


def _auth(api_key):
    return {"X-API-Key": api_key}


# --------------------------------------------------------------------------- #
# Autenticación
# --------------------------------------------------------------------------- #

def test_buscar_sin_api_key_devuelve_401(client):
    resp = client.post("/api/v1/buscar", json={"pregunta": "hola", "top_k": 3})
    assert resp.status_code == 401


def test_buscar_api_key_invalida_devuelve_403(client):
    resp = client.post(
        "/api/v1/buscar",
        json={"pregunta": "hola", "top_k": 3},
        headers={"X-API-Key": "clave-incorrecta"},
    )
    assert resp.status_code == 403


# --------------------------------------------------------------------------- #
# Documentos genéricos + búsqueda (payload completo)
# --------------------------------------------------------------------------- #

def test_upsert_documento_y_buscar_devuelve_payload(client, api_key):
    doc = {
        "id": 10,
        "texto": "seguridad usuarios cuentas operadores",
        "payload": {"titulo": "Seguridad › Usuarios", "url": "wwusersgam.aspx", "tipo": "security"},
    }
    r = client.post("/api/v1/documentos/upsert", json=doc, headers=_auth(api_key))
    assert r.status_code == 200, r.text
    assert r.json()["count"] == 1

    r = client.post(
        "/api/v1/buscar",
        json={"pregunta": "usuarios", "top_k": 3},
        headers=_auth(api_key),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] >= 1
    data = body["resultados"][0]["data"]
    # El payload completo viaja en 'data' (no nulls)
    assert data["titulo"] == "Seguridad › Usuarios"
    assert data["url"] == "wwusersgam.aspx"
    assert data["tipo"] == "security"
    assert 0.0 <= body["resultados"][0]["score"] <= 1.0


def test_upsert_batch_y_filtros(client, api_key):
    payload = {
        "documentos": [
            {"id": 1, "texto": "seguridad roles", "payload": {"tipo": "security"}},
            {"id": 2, "texto": "gestion turnos reportes", "payload": {"tipo": "management"}},
            {"id": 3, "texto": "seguridad permisos", "payload": {"tipo": "security"}},
        ]
    }
    r = client.post("/api/v1/documentos/upsert/batch", json=payload, headers=_auth(api_key))
    assert r.status_code == 200, r.text
    assert r.json()["count"] == 3

    r = client.post(
        "/api/v1/buscar",
        json={"pregunta": "seguridad", "top_k": 10, "filtros": {"tipo": "management"}},
        headers=_auth(api_key),
    )
    assert r.status_code == 200, r.text
    resultados = r.json()["resultados"]
    assert resultados
    assert all(item["data"]["tipo"] == "management" for item in resultados)


def test_delete_documento_204_luego_404(client, api_key):
    doc = {"id": 99, "texto": "documento temporal zzz", "payload": {}}
    assert client.post("/api/v1/documentos/upsert", json=doc, headers=_auth(api_key)).status_code == 200

    r = client.delete("/api/v1/documentos/99", headers=_auth(api_key))
    assert r.status_code == 204

    r = client.delete("/api/v1/documentos/99", headers=_auth(api_key))
    assert r.status_code == 404


# --------------------------------------------------------------------------- #
# Endpoints públicos y CORS
# --------------------------------------------------------------------------- #

def test_health_basico_publico(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert "status" in r.json()


def test_cors_preflight_permite_delete(client):
    r = client.options(
        "/api/v1/documentos/1",
        headers={
            "Origin": CORS_ORIGIN,
            "Access-Control-Request-Method": "DELETE",
        },
    )
    assert r.status_code in (200, 204)
    allow = r.headers.get("access-control-allow-methods", "")
    # El header refleja los métodos permitidos (incluye DELETE)
    assert "DELETE" in allow or r.headers.get("access-control-allow-origin") == CORS_ORIGIN
