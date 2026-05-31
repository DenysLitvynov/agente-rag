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

## Estructura del proyecto

```
agente-rag/
├── consultar.py              # Punto de entrada del contrato (opción A)
├── verificar_imagen.py       # Extra Rekognition: CLI (foto → verificación)
├── corpus/                   # 16 documentos .txt de DNI (no modificar)
├── src/agente_rag/
│   ├── pipeline.py           # Orquestador: retrieve → prompt → generate
│   ├── chunker.py            # Troceo con tratamiento especial Q/A
│   ├── embedder.py           # Cliente embeddings Ollama
│   ├── retriever.py          # ChromaDB: indexación y búsqueda semántica
│   ├── generator.py          # Cliente LLM (Ollama / PoliGPT)
│   ├── prompts.py            # Prompt anti-alucinación
│   ├── rekognition.py        # Extra: OCR (AWS Rekognition) + verificación
│   └── config.py             # Configuración desde .env
├── frontend/
│   └── app.py                # Extra: interfaz web Streamlit (chat + verificar imagen)
├── .streamlit/
│   └── config.toml           # Tema visual del frontend
├── scripts/
│   └── build_index.py        # Construcción del índice vectorial
├── benchmark/
│   ├── preguntas.json        # Set fijo de 12 preguntas
│   ├── benchmark.py          # Script del benchmark
│   ├── benchmark.json        # Resultados crudos
│   └── benchmark.md          # Tabla legible + interpretación
├── evaluacion/               # Banda 8: RAGAs + métricas propias
│   ├── evaluar_ragas.py
│   ├── ground_truth.json
│   ├── metricas_propias.py
│   ├── metricas_propias.md
│   └── ragas_results.json
├── features.json             # Declaración de bandas y extras implementados
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

```

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

### Verificación de imágenes con AWS Rekognition

Sube una foto (un cartel, un horario impreso, un post) y el agente extrae el
texto con **AWS Rekognition** (OCR) y comprueba si coincide con la información
oficial del corpus (COINCIDE / CONTRADICE / SIN INFORMACIÓN), citando fuentes.

Requiere `boto3` (ya en `requirements.txt`) y credenciales de AWS en el `.env`
(`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`).

- **Desde el frontend:** modo "Verificar imagen" → subir foto → "Verificar contra el corpus".
- **Desde la terminal:**

```bash
python verificar_imagen.py ruta/a/la/imagen.jpg
```
