"""Cliente HTTP para embeddings (Ollama).

Hace una llamada por chunk porque el endpoint ``/api/embeddings`` de Ollama
no soporta batching nativo. Para corpus pequeños (< 500 chunks) es asumible.
Si crece, valorad migrar a sentence-transformers en local.
"""

from __future__ import annotations

import urllib3
import requests

from .config import SETTINGS


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def embed(text: str) -> list[float]:
    """Devuelve el embedding de ``text`` usando el modelo configurado."""
    response = requests.post(
        f"{SETTINGS.ollama_url}/embeddings",
        json={"model": SETTINGS.embed_model, "prompt": text},
        verify=SETTINGS.verify_ssl,
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    if "embedding" not in payload:
        raise RuntimeError(f"Respuesta inesperada del embedder: {payload}")
    return payload["embedding"]


def embed_many(texts: list[str]) -> list[list[float]]:
    return [embed(t) for t in texts]
