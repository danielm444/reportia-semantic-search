"""Proveedor de embeddings que delega en el llm-adapter de ReportIA (ADR-0049).

ReportIA centraliza TODA la inferencia en ``reportia-llm-adapter`` (regla
``llm-prompting`` #4, "única puerta a inferencia"). Este provider implementa la
interfaz ``Embeddings`` de LangChain hablando por HTTP al endpoint
``POST /api/v1/embeddings/embed`` del llm-adapter, en lugar de llamar a OpenAI
directamente. Consecuencias:

- el **modelo** de embeddings lo decide el llm-adapter (catálogo
  ``embedding_model``, ADR-0047; default local TEI opt-in), no este servicio;
- con el modelo local el texto del cliente **no sale a internet** (invariante de
  privacidad de ADR-0043 / ADR-0049);
- ``reportia-semantic-search`` queda como puro almacenamiento + búsqueda sobre
  Qdrant, reusable para selección de tablas y para búsqueda de reportes/config.

Contrato del endpoint:
- request:  ``{"inputs": ["texto1", "texto2", ...]}``
- response: ``{"embeddings": [[float, ...], ...], "model_id": str, "dim": int}``
"""

from __future__ import annotations

from typing import Any, Dict, List

import httpx
from langchain_core.embeddings import Embeddings

from app.core.exceptions import EmbeddingServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)

_EMBED_PATH = "/api/v1/embeddings/embed"


class LlmAdapterEmbeddings(Embeddings):
    """Embeddings de LangChain servidos por el llm-adapter de ReportIA (HTTP)."""

    def __init__(self, base_url: str, timeout: float = 60.0):
        if not base_url:
            raise ValueError("LlmAdapterEmbeddings requiere base_url del llm-adapter")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._url = f"{self.base_url}{_EMBED_PATH}"

    # ------------------------------------------------------------------ #
    # Núcleo HTTP
    # ------------------------------------------------------------------ #
    def _post_sync(self, inputs: List[str]) -> List[List[float]]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(self._url, json={"inputs": inputs})
                resp.raise_for_status()
                return self._parse(resp.json(), len(inputs))
        except httpx.HTTPError as exc:
            logger.error("Fallo al embeber vía llm-adapter (sync)", url=self._url, error=str(exc))
            raise EmbeddingServiceError(
                "El llm-adapter no respondió al embeber (¿modelo local opt-in apagado?)",
                original_error=str(exc),
            )

    async def _post_async(self, inputs: List[str]) -> List[List[float]]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(self._url, json={"inputs": inputs})
                resp.raise_for_status()
                return self._parse(resp.json(), len(inputs))
        except httpx.HTTPError as exc:
            logger.error("Fallo al embeber vía llm-adapter (async)", url=self._url, error=str(exc))
            raise EmbeddingServiceError(
                "El llm-adapter no respondió al embeber (¿modelo local opt-in apagado?)",
                original_error=str(exc),
            )

    @staticmethod
    def _parse(payload: Dict[str, Any], expected: int) -> List[List[float]]:
        vectors = payload.get("embeddings")
        got = len(vectors) if isinstance(vectors, list) else None
        if got != expected:
            raise EmbeddingServiceError(
                "Respuesta de embeddings inesperada del llm-adapter",
                original_error=f"esperados {expected} vectores, recibidos {got}",
            )
        return vectors

    # ------------------------------------------------------------------ #
    # Interfaz LangChain Embeddings
    # ------------------------------------------------------------------ #
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return self._post_sync(list(texts))

    def embed_query(self, text: str) -> List[float]:
        return self._post_sync([text])[0]

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return await self._post_async(list(texts))

    async def aembed_query(self, text: str) -> List[float]:
        return (await self._post_async([text]))[0]
