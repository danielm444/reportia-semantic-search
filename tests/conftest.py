"""
Configuración de pytest y fakes para la suite.

La suite corre **sin red ni OpenAI**:
- Embeddings: proveedor determinista (bag-of-words hasheado) que implementa la
  interfaz ``langchain_core.embeddings.Embeddings``. Tokens compartidos → mayor
  similitud coseno, lo que permite testear orden, filtros y umbrales.
- Qdrant: cliente local en memoria (``QdrantClient(location=":memory:")``).
"""

import hashlib
import math
from typing import List

import pytest
from langchain_core.embeddings import Embeddings
from qdrant_client import QdrantClient

from app.services.qdrant_service import QdrantService
from app.services.embedding_service import EmbeddingService
from app.services.search_service import SearchService
import app.services.search_service as search_module
import app.services.embedding_service as embedding_module
import app.services.qdrant_service as qdrant_module
from app.config.settings import settings

# Dimensión pequeña para velocidad
DIM = 64


def _token_index(token: str, dim: int) -> int:
    """Índice determinista y estable entre ejecuciones (no usa hash() salteado)."""
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % dim


class FakeEmbeddings(Embeddings):
    """Embeddings deterministas tipo bag-of-words, normalizados a norma 1."""

    def __init__(self, dim: int = DIM):
        self.dim = dim

    def _vec(self, text: str) -> List[float]:
        v = [0.0] * self.dim
        for token in (text or "").lower().split():
            v[_token_index(token, self.dim)] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._vec(text)

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> List[float]:
        return self._vec(text)


@pytest.fixture
def embedding_service() -> EmbeddingService:
    return EmbeddingService(embeddings_provider=FakeEmbeddings(DIM))


@pytest.fixture
def qdrant_service() -> QdrantService:
    client = QdrantClient(location=":memory:")
    return QdrantService(client=client, collection_name="test_collection")


@pytest.fixture
def search_service(embedding_service, qdrant_service) -> SearchService:
    return SearchService(
        embedding_service=embedding_service,
        qdrant_service=qdrant_service,
        vector_size=DIM,
    )


@pytest.fixture
def api_key() -> str:
    """API key válida (la del entorno de la suite)."""
    return settings.menu_api_key


@pytest.fixture
def client(monkeypatch, search_service, embedding_service, qdrant_service):
    """
    TestClient con los singletons de servicios sustituidos por fakes.

    Se instancia ``TestClient(app)`` SIN context manager para no disparar el
    lifespan (warm-up real contra OpenAI/Qdrant).
    """
    from fastapi.testclient import TestClient
    import main

    monkeypatch.setattr(search_module, "_search_service", search_service)
    monkeypatch.setattr(embedding_module, "_embedding_service", embedding_service)
    monkeypatch.setattr(qdrant_module, "_qdrant_service", qdrant_service)

    return TestClient(main.app)
