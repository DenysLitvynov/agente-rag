"""Punto de entrada del contrato (Opción B — endpoint HTTP).

Sirve ``POST /query`` con el mismo JSON que ``consultar.py``. Si vuestro
``features.json`` declara ``interfaz="endpoint_http"``, este es el módulo
que el corrector levanta.

Arranque local:
    uvicorn api:app --host 127.0.0.1 --port 8000 --reload
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from fastapi import FastAPI  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from agente_rag.config import SETTINGS  # noqa: E402
from agente_rag.pipeline import answer  # noqa: E402


class QueryIn(BaseModel):
    pregunta: str
    conversation_id: str | None = None
    k: int = 5


app = FastAPI(
    title="Agente RAG — GTI Orienta (repo-ejemplo)",
    version="0.1.0",
    description=(
        "Repo-ejemplo del Asistente DNI con caso GTI Orienta. "
        "Cumple el contrato del enunciado §9 (opción B)."
    ),
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "ollama_url": SETTINGS.ollama_url,
        "llm_model": SETTINGS.llm_model,
        "embed_model": SETTINGS.embed_model,
    }


@app.post("/query")
def query(payload: QueryIn) -> dict:
    return answer(payload.pregunta, k=payload.k, conversation_id=payload.conversation_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=SETTINGS.api_host, port=SETTINGS.api_port)
