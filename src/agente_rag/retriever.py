"""Indexación y retrieval con ChromaDB persistente.

ChromaDB en disco (``persistent_client``) nos da dos cosas que el Colab no
tenía: el índice sobrevive entre ejecuciones (no hay que reembedar) y el
arranque de ``consultar.py`` cae a < 2 s tras la primera build. Es lo que
hace falta para superar el oral con el repo recién clonado.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chromadb

from .chunker import Chunk
from .config import SETTINGS
from .embedder import embed


@dataclass
class RetrievedChunk:
    source: str
    text: str
    score: float
    chunk_id: str


def _client(path: Path) -> chromadb.api.ClientAPI:
    path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(path))


def build_index(chunks: list[Chunk]) -> int:
    """Construye (o reemplaza) la colección con ``chunks``.

    Forzamos métrica coseno (``hnsw:space=cosine``). Por defecto ChromaDB
    usa L2 al cuadrado y los scores salen con magnitudes incomparables
    entre queries. Con coseno la distancia está acotada en [0, 2] y
    ``1 - distance`` cae en [-1, 1] — interpretable como similitud.
    """
    client = _client(SETTINGS.chroma_path)
    if SETTINGS.collection_name in [c.name for c in client.list_collections()]:
        client.delete_collection(SETTINGS.collection_name)
    col = client.create_collection(
        SETTINGS.collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    col.add(
        ids=[c.id for c in chunks],
        embeddings=[embed(c.text) for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[{"source": c.source, "chunk_index": c.chunk_index} for c in chunks],
    )
    return col.count()


def _open_collection() -> chromadb.api.models.Collection.Collection:
    client = _client(SETTINGS.chroma_path)
    return client.get_collection(SETTINGS.collection_name)


def retrieve(question: str, *, k: int = 5) -> list[RetrievedChunk]:
    """Top-k semántico. ``score = 1 - distance`` para que más alto = mejor."""
    col = _open_collection()
    q_emb = embed(question)
    res = col.query(query_embeddings=[q_emb], n_results=k)
    out: list[RetrievedChunk] = []
    for i in range(len(res["ids"][0])):
        distance = float(res["distances"][0][i])
        out.append(
            RetrievedChunk(
                source=res["metadatas"][0][i]["source"],
                text=res["documents"][0][i],
                score=round(1.0 - distance, 4),
                chunk_id=res["ids"][0][i],
            )
        )
    return out
