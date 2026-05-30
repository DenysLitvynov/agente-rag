from __future__ import annotations

import json
import math
from pathlib import Path

# Dataset de HuggingFace para construir el dataset de evaluación
from datasets import Dataset

# Función principal de evaluación de RAGAS
from ragas import evaluate

# Métricas estándar de RAGAS
from ragas.metrics import (
    faithfulness,       # fidelidad al contexto
    answer_relevancy,  # relevancia de la respuesta
    context_precision, # calidad de los chunks recuperados
    context_recall,    # cobertura del contexto recuperado
)

# LLM y embeddings locales (Ollama) para que RAGAS no necesite OpenAI
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings

import sys


# Obtiene la raíz del repositorio
REPO_ROOT = Path(__file__).resolve().parents[1]

# Añade la raíz del repo y /src al path para poder importar módulos internos
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))


# Pipeline principal del sistema RAG
from agente_rag.pipeline import answer

# Métricas personalizadas
from evaluacion.metricas_propias import (
    source_citation_accuracy,
    contradiction_handling_score,
)


# Archivo con preguntas y respuestas esperadas
GROUND_TRUTH_FILE = REPO_ROOT / "evaluacion" / "ground_truth.json"


def build_dataset():
    """
    Construye:
    - Dataset compatible con RAGAS
    - Métricas propias del proyecto
    """

    # Lee el JSON de ground truth
    raw = json.loads(GROUND_TRUTH_FILE.read_text(encoding="utf-8"))

    samples = []
    propias = []

    # Recorre cada pregunta de evaluación
    for item in raw:

        pregunta = item["question"]
        gt = item["ground_truth"]

        # Ejecuta el pipeline RAG
        salida = answer(pregunta)

        # Extrae los textos de los chunks recuperados
        contexts = [c["text"] for c in salida["chunks"]]

        # Formato requerido por RAGAS
        samples.append(
            {
                "question": pregunta,
                "answer": salida["respuesta"],
                "contexts": contexts,
                "ground_truth": gt,
            }
        )

        # Métricas personalizadas
        propias.append(
            {
                "question": pregunta,
                "source_citation_accuracy": source_citation_accuracy(salida),
                "contradiction_handling_score":
                    contradiction_handling_score(salida),
            }
        )

    # Convierte la lista a Dataset HuggingFace
    return Dataset.from_list(samples), propias


def main():

    # Construye datos de evaluación
    dataset, propias = build_dataset()

    # Configura LLM y embeddings locales (Ollama) para RAGAS
    # Timeout alto (600s) porque Ollama procesa secuencialmente
    # y los jobs de RAGAS se encolan
    ollama_llm = ChatOllama(
        model="qwen2.5:3b",
        base_url="http://localhost:11434",
        timeout=600,
    )
    ollama_emb = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url="http://localhost:11434",
    )

    # Ejecuta métricas RAGAS con modelos locales de forma secuencial (max_workers=1)
    # y un timeout muy alto (1000s) para garantizar éxito sin Timeouts
    from ragas import RunConfig
    run_config = RunConfig(timeout=1000, max_workers=1)

    result = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ],
        llm=ollama_llm,
        embeddings=ollama_emb,
        run_config=run_config,
        raise_exceptions=False,
    )

    # Convierte el DataFrame a dict limpio (sin numpy/NaN)
    def _clean(obj):
        """Convierte tipos numpy y NaN a tipos nativos de Python."""
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_clean(v) for v in obj]
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        if hasattr(obj, "tolist"):         # numpy array o scalar
            return _clean(obj.tolist())
        return obj

    # Resultado final
    out = _clean({
        "ragas": result.to_pandas().to_dict(),
        "metricas_propias": propias,
    })

    # Guarda resultados en JSON
    out_path = REPO_ROOT / "evaluacion" / "ragas_results.json"

    out_path.write_text(
        json.dumps(out, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    print(f"Resultados guardados en {out_path}")


# Punto de entrada del script
if __name__ == "__main__":
    main()