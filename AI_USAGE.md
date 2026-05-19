# Uso de herramientas de Inteligencia Artificial

## Claude (claude.ai)

**Tareas realizadas:**
- Diagnóstico del problema de configuración del entorno (colección ChromaDB incorrecta, .env no propagado en tiempo de import)
- Diseño e implementación del preprocesado Q/A en `src/agente_rag/chunker.py`
- Redacción y ajuste iterativo del prompt anti-alucinación en `src/agente_rag/prompts.py`
- Actualización del endpoint de embeddings en `src/agente_rag/embedder.py` (migración de `/api/embeddings` a `/api/embed` por cambio de versión en Ollama 0.24)
- Corrección de la carga del `.env` en `scripts/build_index.py` y `benchmark/benchmark.py`
- Implementación del script `benchmark/benchmark.py` con soporte para Ollama local y PoliGPT

**Ficheros modificados con asistencia de IA:**
- `src/agente_rag/chunker.py` — lógica de detección y agrupación de pares Q/A
- `src/agente_rag/prompts.py` — prompt anti-alucinación con reglas estrictas
- `src/agente_rag/embedder.py` — actualización de endpoint Ollama
- `scripts/build_index.py` — carga manual del .env antes de imports
- `benchmark/benchmark.py` — script completo de benchmark

**Revisión posterior:** Todo el código generado fue ejecutado, depurado y verificado manualmente en el entorno real antes de incluirse en el repositorio. Los errores detectados durante la ejecución (endpoints incorrectos, colección no encontrada, modelos no descargados) fueron diagnosticados y corregidos de forma iterativa.

**Partes del código sin revisión posterior:** Ninguna.
