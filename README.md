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
## Frontend (extra) — Streamlit

Interfaz web ligera que **consume el contrato del agente**: importa la función
`consultar()` de `consultar.py` (opción A) y se limita a presentar el resultado,
sin reimplementar nada del dominio. Por cada pregunta muestra la respuesta, las
**fuentes citadas** (banda 6), los **chunks recuperados con su score** (banda 7)
y las **métricas** de generación (latencia, tokens/s, modelo).

### Requisitos

- Dependencias del proyecto instaladas (`pip install -r requirements.txt`);
  `streamlit` ya está incluido.
- Ollama en marcha y el índice construido (`python scripts/build_index.py`),
  exactamente igual que para usar `consultar.py`.

### Cómo lanzarlo

Desde la **raíz del repositorio**:

```bash
streamlit run frontend/app.py
```

Se abre solo en el navegador (`http://localhost:8501`). La primera respuesta
tarda más porque el modelo se carga en memoria; en CPU la generación va a la
velocidad esperable de un modelo local.

### Qué incluye

- Chat con historial de la sesión y preguntas de ejemplo (incluida una fuera de
  ámbito, para ver que el agente la rechaza).
- Respuesta + fuentes citadas + desplegable con los chunks recuperados y sus
  scores + métricas de generación.
- Barra lateral con la configuración activa (modelo LLM, embeddings, colección).
- Tema visual definido en `.streamlit/config.toml`.

### Estructura

```
frontend/
└── app.py          # UI Streamlit (importa consultar())
.streamlit/
└── config.toml     # tema visual (colores y tipografía)
```

