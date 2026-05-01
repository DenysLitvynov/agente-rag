"""Agente RAG — repo-ejemplo del Asistente DNI (caso GTI Orienta).

Estructura del paquete:
- config: variables de entorno y constantes.
- chunker: troceo de los .txt del corpus.
- embedder: cliente HTTP para embeddings (Ollama).
- retriever: ChromaDB persistente + retrieval semántico.
- generator: cliente HTTP para generación (Ollama) con métricas.
- prompts: plantilla anti-alucinación con cita de fuentes.
- pipeline: orquestador percibir → decidir → actuar.
"""

__version__ = "0.1.0"
