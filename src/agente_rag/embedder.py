"""Cliente HTTP para embeddings (Ollama).
Compatible con Ollama >= 0.2 que usa /api/embed con campo 'input'.
"""
from __future__ import annotations
import urllib3
import requests
from .config import SETTINGS

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def embed(text: str) -> list[float]:
    """Devuelve el embedding de ``text`` usando el modelo configurado."""
    response = requests.post(
        f"{SETTINGS.ollama_url}/embed",
        json={"model": SETTINGS.embed_model, "input": text},
        verify=SETTINGS.verify_ssl,
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    # Ollama >= 0.2 devuelve {"embeddings": [[...]]}
    if "embeddings" in payload:
        return payload["embeddings"][0]
    # fallback por si acaso
    if "embedding" in payload:
        return payload["embedding"]
    raise RuntimeError(f"Respuesta inesperada del embedder: {payload}")


def embed_many(texts: list[str]) -> list[list[float]]:
    return [embed(t) for t in texts]