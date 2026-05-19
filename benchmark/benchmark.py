"""Benchmark de 4 modelos sobre el corpus DNI.

Ejecuta el mismo set de preguntas contra:
- 2 modelos locales via Ollama
- 2 modelos via PoliGPT

Genera benchmark/benchmark.json con métricas crudas.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Cargar .env ANTES de cualquier import del paquete
_ROOT = Path(__file__).resolve().parents[1]
_env_path = _ROOT / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# Ahora sí importamos el paquete
sys.path.insert(0, str(_ROOT / "src"))

import requests
from agente_rag.retriever import retrieve
from agente_rag.prompts import build_prompt

PREGUNTAS_PATH = Path(__file__).parent / "preguntas.json"
OUTPUT_PATH = Path(__file__).parent / "benchmark.json"

MODELOS = [
    {"alias": "qwen2.5:3b",   "servidor": "ollama_local"},
    {"alias": "llama3.2:3b",  "servidor": "ollama_local"},
    {"alias": "gemma3:27b",   "servidor": "poligpt"},
    {"alias": "llama3.3:70b", "servidor": "poligpt"},
]

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api")
POLIGPT_URL = os.getenv("POLIGPT_BASE_URL", "https://api.poligpt.upv.es/v1")
POLIGPT_KEY = os.getenv("POLIGPT_API_KEY", "")

def llamar_ollama(prompt: str, model: str) -> dict:
    t0 = time.time()
    r = requests.post(
        f"{OLLAMA_URL}/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2}
        },
        timeout=300,
    )
    elapsed = time.time() - t0
    r.raise_for_status()
    payload = r.json()
    prompt_tokens = int(payload.get("prompt_eval_count", 0))
    output_tokens = int(payload.get("eval_count", 0))
    eval_ns = int(payload.get("eval_duration", 0))
    tps = output_tokens / (eval_ns / 1e9) if eval_ns > 0 else 0.0
    return {
        "texto": payload["response"].strip(),
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "tokens_per_sec": round(tps, 2),
        "latencia_s": round(elapsed, 2),
    }

def llamar_poligpt(prompt: str, model: str) -> dict:
    t0 = time.time()
    r = requests.post(
        f"{POLIGPT_URL}/chat/completions",
        headers={"Authorization": f"Bearer {POLIGPT_KEY}"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        },
        timeout=300,
        verify=False,
    )
    elapsed = time.time() - t0
    r.raise_for_status()
    payload = r.json()
    usage = payload.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    tps = output_tokens / elapsed if elapsed > 0 else 0.0
    texto = payload["choices"][0]["message"]["content"].strip()
    return {
        "texto": texto,
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "tokens_per_sec": round(tps, 2),
        "latencia_s": round(elapsed, 2),
    }


def evaluar_respuesta(texto: str, ambito: str) -> str:
    """Evaluación subjetiva simple."""
    if ambito == "fuera_ambito":
        if "no tengo" in texto.lower() or "no está" in texto.lower():
            return "acierto"
        return "fallo"
    if len(texto.strip()) < 10:
        return "fallo"
    if "no tengo esa información" in texto.lower() and ambito != "fuera_ambito":
        return "fallo"
    return "acierto"


def main():
    preguntas = json.loads(PREGUNTAS_PATH.read_text(encoding="utf-8"))
    resultados = []

    for modelo in MODELOS:
        alias = modelo["alias"]
        servidor = modelo["servidor"]
        print(f"\n{'='*50}")
        print(f"Modelo: {alias} ({servidor})")
        print(f"{'='*50}")

        for q in preguntas:
            print(f"  [{q['id']}] {q['pregunta'][:60]}...")
            try:
                # Retrieval (igual para todos los modelos)
                chunks = retrieve(q["pregunta"], k=5)
                prompt = build_prompt(q["pregunta"], chunks)

                # Generación según servidor
                if servidor == "ollama_local":
                    gen = llamar_ollama(prompt, alias)
                else:
                    gen = llamar_poligpt(prompt, alias)

                calidad = evaluar_respuesta(gen["texto"], q["ambito"])
                print(f"    → {calidad} | {gen['latencia_s']}s | {gen['output_tokens']} tokens")

                resultados.append({
                    "modelo": alias,
                    "servidor": servidor,
                    "pregunta_id": q["id"],
                    "pregunta": q["pregunta"],
                    "ambito": q["ambito"],
                    "respuesta": gen["texto"],
                    "prompt_tokens": gen["prompt_tokens"],
                    "output_tokens": gen["output_tokens"],
                    "tokens_per_sec": gen["tokens_per_sec"],
                    "latencia_s": gen["latencia_s"],
                    "calidad": calidad,
                })

            except Exception as e:
                print(f"    ERROR: {e}")
                resultados.append({
                    "modelo": alias,
                    "servidor": servidor,
                    "pregunta_id": q["id"],
                    "pregunta": q["pregunta"],
                    "ambito": q["ambito"],
                    "respuesta": f"ERROR: {e}",
                    "prompt_tokens": 0,
                    "output_tokens": 0,
                    "tokens_per_sec": 0,
                    "latencia_s": 0,
                    "calidad": "error",
                })

    OUTPUT_PATH.write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nResultados guardados en {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
