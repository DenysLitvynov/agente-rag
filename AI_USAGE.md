# Uso de herramientas de Inteligencia Artificial

## Claude (claude.ai)

**Tareas realizadas:**
- Diagnóstico del problema de configuración del entorno (colección ChromaDB incorrecta, .env no propagado en tiempo de import)
- Diseño e implementación del preprocesado Q/A en `src/agente_rag/chunker.py`
- Redacción y ajuste iterativo del prompt anti-alucinación en `src/agente_rag/prompts.py`
- Actualización del endpoint de embeddings en `src/agente_rag/embedder.py` (migración de `/api/embeddings` a `/api/embed` por cambio de versión en Ollama 0.24)
- Corrección de la carga del `.env` en `scripts/build_index.py` y `benchmark/benchmark.py`
- Implementación del script `benchmark/benchmark.py` con soporte para Ollama local y PoliGPT
- Diseño e implementación del frontend web con Streamlit (`frontend/app.py`): interfaz que consume el contrato `consultar()` sin reimplementar el dominio, con dos modos (chat y verificación de imágenes), mostrando respuesta, fuentes citadas, chunks con score y métricas de generación
- Tema visual del frontend en `.streamlit/config.toml`
- Implementación del extra de AWS Rekognition (`src/agente_rag/rekognition.py`): OCR de imágenes con `boto3` (`detect_text`) y verificación del texto extraído contra el corpus, reutilizando el retriever y el generador del agente (veredicto COINCIDE / CONTRADICE / SIN INFORMACIÓN con cita de fuentes)
- Script CLI de prueba del extra (`verificar_imagen.py`) para validar el flujo OCR → recuperación → verificación de forma aislada
- Ajuste del parámetro `k` de recuperación en el flujo de verificación de imágenes para mejorar la cobertura de chunks
- Manejo de errores amigable (credenciales AWS, modelo no encontrado, conexión con Ollama) en el frontend y el módulo de Rekognition

**Ficheros modificados con asistencia de IA:**
- `src/agente_rag/chunker.py` — lógica de detección y agrupación de pares Q/A
- `src/agente_rag/prompts.py` — prompt anti-alucinación con reglas estrictas
- `src/agente_rag/embedder.py` — actualización de endpoint Ollama
- `scripts/build_index.py` — carga manual del .env antes de imports
- `benchmark/benchmark.py` — script completo de benchmark
- `frontend/app.py` — interfaz Streamlit (chat + verificación de imágenes) [nuevo]
- `.streamlit/config.toml` — tema visual del frontend [nuevo]
- `src/agente_rag/rekognition.py` — OCR con AWS Rekognition + verificación contra el corpus [nuevo]
- `verificar_imagen.py` — CLI de prueba del extra de Rekognition [nuevo]

**Revisión posterior:** Todo el código generado fue ejecutado, depurado y verificado manualmente en el entorno real antes de incluirse en el repositorio. Los errores detectados durante la ejecución (endpoints incorrectos, colección no encontrada, modelos no descargados) fueron diagnosticados y corregidos de forma iterativa.

Los extras (frontend Streamlit y verificación con AWS Rekognition) se ejecutaron y probaron en el entorno real: se verificó el OCR sobre imágenes de prueba y el funcionamiento de los modos de chat y de verificación de imágenes contra el corpus.

**Partes del código sin revisión posterior:** Ninguna.
