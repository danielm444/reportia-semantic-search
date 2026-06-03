#!/usr/bin/env python3
"""
Smoke test de integración EN VIVO contra el contenedor real de Qdrant.

Verifica end-to-end: indexación de data/menu.json, búsqueda semántica con
filtros/paginación, y la API HTTP completa (auth incluida) vía TestClient.

NOTA: el proveedor de embeddings de OpenAI se sustituye por uno determinista
(bag-of-words hasheado) porque la cuenta de OpenAI no tiene cuota (429). Esto
ejercita TODO el sistema real (Qdrant en modo servidor, servicios, FastAPI,
auth) salvo la llamada al vendor de embeddings.
"""

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.embeddings import Embeddings
from app.config.settings import settings
from app.services.qdrant_service import QdrantService
from app.services.embedding_service import EmbeddingService
from app.services.search_service import SearchService
import app.services.search_service as ss
import app.services.embedding_service as es
import app.services.qdrant_service as qs
from app.models.search_models import MenuItem

DIM = 64
COLLECTION = "menu_demo"


class FakeEmbeddings(Embeddings):
    """Embeddings deterministas (BoW hasheado) — sustituto de OpenAI por falta de cuota."""

    def __init__(self, dim: int = DIM):
        self.dim = dim

    def _vec(self, text: str) -> List[float]:
        v = [0.0] * self.dim
        for tok in (text or "").lower().split():
            idx = int.from_bytes(hashlib.blake2b(tok.encode(), digest_size=8).digest(), "big") % self.dim
            v[idx] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def embed_documents(self, texts): return [self._vec(t) for t in texts]
    def embed_query(self, text): return self._vec(text)
    async def aembed_documents(self, texts): return self.embed_documents(texts)
    async def aembed_query(self, text): return self._vec(text)


def banner(msg):
    print("\n" + "=" * 70)
    print(msg)
    print("=" * 70)


async def main():
    banner("1) Conexión REAL a Qdrant + servicios (embeddings deterministas)")
    emb = EmbeddingService(embeddings_provider=FakeEmbeddings(DIM))
    qdr = QdrantService(collection_name=COLLECTION)  # url real desde settings
    health = qdr.health_check()
    print(f"Qdrant: status={health['status']} url={health['url']}")
    assert health["status"] == "healthy", "Qdrant no está sano"

    svc = SearchService(embedding_service=emb, qdrant_service=qdr, vector_size=DIM)
    # Inyectar singletons para que la API HTTP use estos mismos servicios
    ss._search_service = svc
    es._embedding_service = emb
    qs._qdrant_service = qdr

    banner("2) Indexar data/menu.json en Qdrant (scorched earth + lote)")
    data = json.loads(Path("data/menu.json").read_text(encoding="utf-8"))
    items = [MenuItem(**_normalize(d)) for d in data]
    documents = [
        {
            "id": it.get_effective_id(),
            "texto": it.to_search_text(),
            "payload": {
                "titulo": it.titulo or it.Nivel0,
                "Nivel0": it.Nivel0,
                "Descripcion": it.get_effective_description(),
                "url": it.url,
                "tipo": it.tipo,
                "estado": it.get_effective_status(),
            },
        }
        for it in items
    ]
    qdr.recreate_collection(vector_size=DIM)
    result = await svc.upsert_documents(documents)
    info = qdr.get_collection_info()
    print(f"Indexados: {result['count']} | points_count en Qdrant: {info.get('points_count')}")
    assert result["count"] == len(documents) == info.get("points_count")

    banner("3) Búsqueda semántica directa (payload completo)")
    for q in ["usuarios", "reportes turnos", "feriados"]:
        res = await svc.search(q, top_k=3)
        print(f"\nQuery: {q!r}")
        for r in res:
            print(f"  score={r['score']:.4f}  {r['data'].get('titulo')}  [{r['data'].get('tipo')}]")

    banner("4) Filtro por payload (tipo=security) + paginación")
    res = await svc.search("usuarios", top_k=5, filters={"tipo": "security"})
    print(f"Resultados tipo=security: {len(res)}")
    assert all(r["data"]["tipo"] == "security" for r in res)
    p1 = await svc.search("seguridad", top_k=1, offset=0)
    p2 = await svc.search("seguridad", top_k=1, offset=1)
    print(f"Paginación: page1={p1[0]['data']['titulo']!r}  page2={p2[0]['data']['titulo']!r}")
    assert p1[0]["data"]["id"] != p2[0]["data"]["id"]

    banner("5) API HTTP real vía TestClient (auth + búsqueda + CRUD)")
    from fastapi.testclient import TestClient
    import main as main_module
    client = TestClient(main_module.app)
    key = {"X-API-Key": settings.menu_api_key}

    r = client.post("/api/v1/buscar", json={"pregunta": "donde gestiono usuarios", "top_k": 2})
    print(f"Sin API key -> {r.status_code} (esperado 401)")
    assert r.status_code == 401

    r = client.post("/api/v1/buscar", json={"pregunta": "donde gestiono usuarios", "top_k": 2}, headers=key)
    print(f"Con API key -> {r.status_code} (esperado 200)")
    body = r.json()
    print(f"  total={body['total']}  top={body['resultados'][0]['data'].get('titulo')!r}  score={body['resultados'][0]['score']}")
    assert r.status_code == 200 and body["total"] >= 1

    # Upsert genérico + verificación + delete
    r = client.post("/api/v1/documentos/upsert",
                    json={"id": 9001, "texto": "documento de prueba smoke zzz", "payload": {"tipo": "demo"}},
                    headers=key)
    print(f"Upsert documento -> {r.status_code} count={r.json().get('count')}")
    r = client.delete("/api/v1/documentos/9001", headers=key)
    print(f"Delete documento -> {r.status_code} (esperado 204)")
    r = client.delete("/api/v1/documentos/9001", headers=key)
    print(f"Delete de nuevo -> {r.status_code} (esperado 404)")

    r = client.get("/api/v1/health", headers=key)
    print(f"Health -> {r.status_code} status={r.json().get('status')}")

    banner("✅ SMOKE TEST EN VIVO: OK")


def _normalize(d):
    n = dict(d)
    if "id" in d and "ID" not in d:
        n["ID"] = d["id"]
    if isinstance(d.get("nivel"), list) and d["nivel"]:
        n.setdefault("Nivel0", d["nivel"][0])
        if len(d["nivel"]) > 1:
            n.setdefault("Nivel1", d["nivel"][1])
    if "descripcion" in d and "Descripcion" not in d:
        n["Descripcion"] = d["descripcion"]
    return n


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
