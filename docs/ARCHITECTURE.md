# Decisiones de arquitectura

> Documento corto que explica el **por qué** detrás de cada elección.
> No describe **qué** hace cada fichero (eso lo cuenta el código y el
> README). Aquí va lo que un alumno no puede deducir leyendo el árbol.

## 1. Por qué single-agent y no hexagonal

Este repo es **plantilla pedagógica**, no aspirante a banda 10. Si os
diéramos la versión hexagonal terminada, regalaríamos los puntos del
techo. El propio enunciado §13 deja el 10 como ejercicio del alumno.

A cambio, este repo deja **muy claro qué refactorizar**:

- `src/agente_rag/embedder.py`, `retriever.py`, `generator.py` ya están
  separados como módulos — son los **futuros adapters**.
- `src/agente_rag/pipeline.py` es el **futuro `domain/chatbot_service.py`**.
- `src/agente_rag/config.py` es la **semilla del composition root**.

La diferencia con un hexagonal real está en las dependencias: ahora
`pipeline.py` *importa* `retriever` y `generator` directamente (acoplamiento
hacia adapters concretos). En hexagonal, `pipeline.py` recibiría dos
**ports** por constructor y no sabría si detrás hay Ollama o un fake.

## 2. Por qué ChromaDB persistente y no in-memory como el Colab

El Colab usa `chromadb.Client()` (in-memory) porque cada celda se ejecuta en
una sesión efímera. En vuestro repo el examinador clona, indexa **una vez**,
y luego hace múltiples preguntas. Reembedar 4 × 27 chunks cada vez son ~30 s
extra que **se pagan en la oral** delante del profesor. Con
`PersistentClient(path=...)` el segundo arranque cae a < 2 s.

Coste: el directorio `data/chroma/` está en `.gitignore`. **Hay que regenerarlo**
en cada portátil — ese es justo el comando que probaréis en el oral
(`python scripts/build_index.py`).

## 3. Por qué `nomic-embed-text` y no sentence-transformers

`nomic-embed-text` viene en el catálogo de Ollama UPV → un único endpoint
para LLM y embeddings. Una sola dependencia (`requests`), un solo timeout
para configurar, un solo error para diagnosticar.

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` es alternativa
válida y **funciona sin red** (descarga el modelo una vez). Lo dejamos
documentado en `manual_desarrollador.pdf §1.2` como opción si Ollama UPV
está caído.

## 4. Por qué chunk_size=500 / overlap=100

Es el "sweet spot" del Colab §3 para texto en español:

- 100: pierde contexto, recupera trozos inconexos.
- 2000: el embedding se diluye y el prompt se infla.
- 500/100: un chunk típico es un párrafo o medio. Suficiente para que el
  retrieval semántico distinga "Inteligencia Artificial" de "Visión Artificial"
  por contexto, no por nombre.

Si vuestro retrieval falla, **lo primero a tocar son estos dos números**.

## 5. Por qué `score = 1 - distance` en `retriever.py`

ChromaDB devuelve **distancias** (más bajo = más cercano). El contrato del
enunciado y el lenguaje natural del informe esperan **scores** (más alto =
mejor match). Hacemos la conversión una sola vez en el adapter para que el
dominio razone siempre en "score" y no en "distance".

## 6. Por qué `verify_ssl=False` SOLO contra UPV

El endpoint Ollama UPV usa cert autofirmado: con `verify=True` falla la
handshake. Con `verify=False` el handshake pasa pero **se desactivan las
comprobaciones de identidad** — cualquier MITM en la red podría suplantar
el endpoint. Es asumible **dentro de la red UPV**, no en general. Por eso
el default en `.env.example` es `VERIFY_SSL=true` y solo se baja en el
caso documentado.

## 7. Por qué los tests no llaman a Ollama

Tres razones:

1. **Reproducibilidad**: el CI no tiene acceso a Ollama. Si los tests
   dependieran de la red, romperían en cada PR.
2. **Velocidad**: un test que llama al LLM tarda 1-2 s. Con 50 tests, son
   minutos. Con stubs, son milisegundos.
3. **Cobertura del contrato sin coste de tokens**: lo importante es
   verificar la **forma** del JSON de salida, no el contenido.

La validación E2E con Ollama real **se hace a mano**: `python scripts/run_eval.py`
+ leer los outputs en `benchmark/runs/`. Eso es lo que el alumno presentará
en el informe.

## 8. Decisiones que NO tomamos a propósito

- **No incluimos retrieval híbrido (BM25 + semántico)**. Está en
  `requirements.txt` (`rank-bm25`) pero no se usa. Es el primer extra
  natural para subir nota: añadir `bm25.py` y mezclar scores.
- **No incluimos memoria conversacional**. El contrato acepta
  `conversation_id` pero el pipeline no la usa. Otro extra abierto.
- **No incluimos frontend**. El extra "frontend +1.5" se hace encima de
  este repo, no dentro: añadid un `streamlit_app.py` que llame a
  `consultar.consultar(...)`.
