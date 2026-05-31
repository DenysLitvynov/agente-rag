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

## Evaluación RAGAs y Métricas Propias (Banda 8)

El proyecto incluye un pipeline completo para la evaluación cuantitativa y cualitativa del sistema RAG utilizando el framework **RAGAs** junto con métricas personalizadas de robustez y precisión de atribución.

### Prerrequisitos

Antes de ejecutar la evaluación, asegúrate de haber completado todos los pasos de la sección **Instalación**:

1. Entorno virtual activado (`.venv`)
2. Dependencias base instaladas (`pip install -r requirements.txt` — ya incluye `ragas` y `datasets`)
3. Fichero `.env` configurado (copiado desde `.env.example`)
4. Modelos de Ollama descargados (`ollama pull nomic-embed-text` y `ollama pull qwen2.5:3b`)
5. Índice vectorial construido (`python scripts/build_index.py`)

Además, instala los paquetes adicionales de LangChain necesarios para que RAGAs use Ollama como juez local:

```bash
pip install langchain langchain-community langchain-openai
```

### Ejecutar la Evaluación

```bash
python evaluacion/evaluar_ragas.py
```

> [!IMPORTANT]
> **Nota sobre el rendimiento local:** El script está configurado para ejecutarse en modo secuencial (`max_workers=1`) y con un timeout alto (`timeout=1000`). Esto garantiza que Ollama (ejecutándose en CPU) procese las consultas una por una sin provocar timeouts ni valores nulos. El proceso completo tarda aproximadamente **1 hora y 45 minutos** en CPU.

### Ficheros Generados

| Fichero | Contenido |
|---------|-----------|
| `evaluacion/ragas_results.json` | Resultados numéricos de las 4 métricas RAGAs (*Faithfulness*, *Answer Relevancy*, *Context Precision*, *Context Recall*) + métricas propias, desglosados por pregunta |
| `evaluacion/metricas_propias.md` | Definición, justificación y valores de las 2 métricas propias (*Source Citation Accuracy* y *Contradiction Handling Score*) |
| `evaluacion/ground_truth.json` | Dataset de 5 preguntas con respuestas de referencia redactadas manualmente |
| `benchmark.md` | Tabla global con todos los resultados RAGAs y métricas propias integrados + interpretación |
