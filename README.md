# Agente RAG — Asistente DNI Valencia

Agente de Retrieval-Augmented Generation que responde preguntas sobre la asociación **DNI (Damos Nuestra Ilusión)** Valencia usando exclusivamente la información de los 16 documentos oficiales proporcionados.

## Requisitos

- Python 3.10+
- [Ollama](https://ollama.com/download) instalado y en ejecución
- Modelos Ollama descargados (ver instalación)
- Acceso a VPN UPV + API key de PoliGPT (solo para benchmark con modelos PoliGPT)

## Instalación

```bash
git clone <url-del-repo>
cd agente-rag

python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

Copia `.env.example` a `.env` y rellena los valores:

```bash
cp .env.example .env
```

Descarga los modelos necesarios con Ollama:

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:3b
ollama pull llama3.2:3b
```

## Construcción del índice

Ejecutar una única vez (o cuando cambie el corpus):

```bash
python scripts/build_index.py
```

Esto lee los 16 `.txt` de `corpus/`, los trocea, genera embeddings con `nomic-embed-text` y los indexa en ChromaDB en `data/chroma/`.

## Uso

```bash
python consultar.py "¿Qué es DNI?"
```

O desde Python:

```python
from consultar import consultar

resultado = consultar("¿Cómo me apunto a los desayunos solidarios?")
print(resultado["respuesta"])
print(resultado["fuentes"])
```

El diccionario devuelto contiene: `respuesta`, `fuentes`, `chunks`, `metricas`, `trazas`.

## Benchmark

```bash
python benchmark/benchmark.py
```

Ejecuta 12 preguntas contra 4 modelos (2 locales + 2 PoliGPT). Requiere VPN UPV activa para los modelos PoliGPT. Genera `benchmark/benchmark.json` y debe completarse con `benchmark/benchmark.md`.

## Estructura del proyecto

```
agente-rag/
├── consultar.py              # Punto de entrada del contrato (opción A)
├── corpus/                   # 16 documentos .txt de DNI (no modificar)
├── src/agente_rag/
│   ├── pipeline.py           # Orquestador: retrieve → prompt → generate
│   ├── chunker.py            # Troceo con tratamiento especial Q/A
│   ├── embedder.py           # Cliente embeddings Ollama
│   ├── retriever.py          # ChromaDB: indexación y búsqueda semántica
│   ├── generator.py          # Cliente LLM (Ollama / PoliGPT)
│   ├── prompts.py            # Prompt anti-alucinación
│   └── config.py             # Configuración desde .env
├── scripts/
│   └── build_index.py        # Construcción del índice vectorial
├── benchmark/
│   ├── preguntas.json        # Set fijo de 12 preguntas
│   ├── benchmark.py          # Script del benchmark
│   ├── benchmark.json        # Resultados crudos
│   └── benchmark.md          # Tabla legible + interpretación
├── features.json             # Declaración de bandas implementadas
├── .env.example              # Plantilla de variables de entorno
├── GRUPO.md                  # Integrantes y roles
└── AI_USAGE.md               # Uso honesto de herramientas IA
```

## Variables de entorno (.env)

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `OLLAMA_URL` | URL del servidor Ollama | `http://localhost:11434/api` |
| `LLM_MODEL` | Modelo LLM para generación | `qwen2.5:3b` |
| `EMBED_MODEL` | Modelo de embeddings | `nomic-embed-text` |
| `COLLECTION_NAME` | Nombre colección ChromaDB | `dni` |
| `CORPUS_DIR` | Directorio del corpus | `corpus` |
| `CHROMA_PATH` | Directorio de ChromaDB | `data/chroma` |
| `POLIGPT_API_KEY` | API key de PoliGPT (UPV) | — |
| `POLIGPT_BASE_URL` | URL base de PoliGPT | `https://api.poligpt.upv.es/v1` |

## Evaluación RAGAs (Banda 8)

Instalar dependencias (funciona bien con Python 3.11):

```bash
pip install ragas datasets langchain langchain-community langchain-openai
```

Ejecutar evaluación:

```bash
python evaluacion/evaluar_ragas.py
```

Los resultados se guardan en:

```text
evaluacion/ragas_results.json

```
