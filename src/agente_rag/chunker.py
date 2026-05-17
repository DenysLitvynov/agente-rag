"""Troceo del corpus DNI.
Combina dos estrategias:
- Archivos con formato Q:/A: se preprocesan agrupando cada par antes de
  pasar por el splitter, evitando que un chunk corte entre pregunta y respuesta.
- Archivos narrativos usan RecursiveCharacterTextSplitter estándar (500, 100).
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class Chunk:
    id: str
    text: str
    source: str
    chunk_index: int


def load_corpus(corpus_dir: Path) -> list[dict]:
    if not corpus_dir.exists():
        raise FileNotFoundError(f"Corpus no encontrado en {corpus_dir}")
    docs = []
    for path in sorted(corpus_dir.glob("*.txt")):
        docs.append({"name": path.name, "text": path.read_text(encoding="utf-8")})
    if not docs:
        raise RuntimeError(f"No hay .txt en {corpus_dir}")
    return docs


def _es_formato_qa(texto: str) -> bool:
    lineas = texto.split('\n')
    lineas_q = sum(1 for l in lineas if l.strip().startswith("Q:"))
    return lineas_q >= 3


def _split_qa(texto: str) -> list[str]:
    bloques = []
    par_actual = []
    for linea in texto.split('\n'):
        linea_strip = linea.strip()
        if linea_strip.startswith("Q:"):
            if par_actual:
                bloques.append('\n'.join(par_actual))
            par_actual = [linea_strip]
        elif linea_strip.startswith("A:") and par_actual:
            par_actual.append(linea_strip)
            bloques.append('\n'.join(par_actual))
            par_actual = []
        elif par_actual:
            par_actual.append(linea_strip)
    if par_actual:
        bloques.append('\n'.join(par_actual))
    return [b for b in bloques if b.strip()]


def split_documents(
    docs: list[dict],
    *,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks: list[Chunk] = []
    for doc in docs:
        texto = doc["text"]
        nombre = doc["name"]
        if _es_formato_qa(texto):
            piezas = _split_qa(texto)
        else:
            piezas = splitter.split_text(texto)
        for i, pieza in enumerate(piezas):
            chunks.append(
                Chunk(
                    id=f"{nombre}__chunk_{i:04d}",
                    text=pieza,
                    source=nombre,
                    chunk_index=i,
                )
            )

    # Descartar chunks demasiado cortos (títulos sueltos sin contenido)
    chunks = [c for c in chunks if len(c.text.strip()) >= 80]

    # Reindexar tras el filtrado
    reindexed = []
    for source, group in groupby(chunks, key=lambda c: c.source):
        for new_idx, chunk in enumerate(group):
            reindexed.append(Chunk(
                id=f"{chunk.source}__chunk_{new_idx:04d}",
                text=chunk.text,
                source=chunk.source,
                chunk_index=new_idx,
            ))
    return reindexed