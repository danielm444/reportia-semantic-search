"""Tests del proveedor de embeddings vía llm-adapter (ADR-0049).

Sin red: se mockean los POST HTTP (``_post_sync``/``_post_async``). El parseo de
la respuesta del llm-adapter se testea directo.
"""

import pytest

from app.core.exceptions import EmbeddingServiceError
from app.services.llm_adapter_embeddings import LlmAdapterEmbeddings


def test_url_construida_bien():
    emb = LlmAdapterEmbeddings("http://reportia-llm-adapter:8003/")
    assert emb._url == "http://reportia-llm-adapter:8003/api/v1/embeddings/embed"


def test_requiere_base_url():
    with pytest.raises(ValueError):
        LlmAdapterEmbeddings("")


def test_parse_ok():
    emb = LlmAdapterEmbeddings("http://x")
    vecs = emb._parse({"embeddings": [[0.1, 0.2]], "model_id": "bge-m3", "dim": 2}, expected=1)
    assert vecs == [[0.1, 0.2]]


def test_parse_count_mismatch_levanta():
    emb = LlmAdapterEmbeddings("http://x")
    with pytest.raises(EmbeddingServiceError):
        emb._parse({"embeddings": [[0.1]]}, expected=2)


def test_parse_shape_invalido_levanta():
    emb = LlmAdapterEmbeddings("http://x")
    with pytest.raises(EmbeddingServiceError):
        emb._parse({"model_id": "x"}, expected=1)


def test_embed_documents_vacio_no_llama_red(monkeypatch):
    emb = LlmAdapterEmbeddings("http://x")

    def _boom(_inputs):
        raise AssertionError("no debería llamar a la red para lista vacía")

    monkeypatch.setattr(emb, "_post_sync", _boom)
    assert emb.embed_documents([]) == []


def test_embed_query_devuelve_primer_vector(monkeypatch):
    emb = LlmAdapterEmbeddings("http://x")
    monkeypatch.setattr(emb, "_post_sync", lambda inputs: [[1.0, 2.0]])
    assert emb.embed_query("hola") == [1.0, 2.0]


def test_embed_documents_pasa_textos(monkeypatch):
    emb = LlmAdapterEmbeddings("http://x")
    captured = {}

    def _fake(inputs):
        captured["inputs"] = inputs
        return [[0.0]] * len(inputs)

    monkeypatch.setattr(emb, "_post_sync", _fake)
    out = emb.embed_documents(["a", "b", "c"])
    assert captured["inputs"] == ["a", "b", "c"]
    assert len(out) == 3


async def test_aembed_query_devuelve_primer_vector(monkeypatch):
    emb = LlmAdapterEmbeddings("http://x")

    async def _fake(_inputs):
        return [[3.0, 4.0]]

    monkeypatch.setattr(emb, "_post_async", _fake)
    assert await emb.aembed_query("hola") == [3.0, 4.0]


async def test_aembed_documents_vacio_no_llama_red(monkeypatch):
    emb = LlmAdapterEmbeddings("http://x")

    async def _boom(_inputs):
        raise AssertionError("no debería llamar a la red para lista vacía")

    monkeypatch.setattr(emb, "_post_async", _boom)
    assert await emb.aembed_documents([]) == []
