# Benchmark — Agente RAG DNI

## Configuración del benchmark

- **Set de preguntas:** 12 preguntas fijas en `benchmark/preguntas.json`
- **Ámbitos cubiertos:** factual, factual con contradicción entre documentos, logística, síntesis multi-documento, fuera de ámbito
- **Pipeline constante:** chunking Q/A + ChromaDB coseno + nomic-embed-text + k=5 (idéntico para los 4 modelos)
- **Solo varía:** el modelo LLM de generación
- **Criterio de calidad subjetiva:** "acierto" si la respuesta usa información real del contexto o rechaza correctamente una pregunta fuera de ámbito; "fallo" si inventa, omite información clave disponible en el corpus, o rechaza una pregunta que sí tenía respuesta

---

## Resultados por modelo y pregunta

| ID | Pregunta | qwen2.5:3b | llama3.2:3b | gemma3:27b | llama3.3:70b |
|----|----------|-----------|------------|-----------|-------------|
| q01 | ¿Qué es DNI? | ✅ | ❌ | ✅ | ✅ |
| q02 | ¿A qué hora son los desayunos? | ✅ | ✅ | ✅ | ✅ |
| q03 | ¿Cómo me apunto a desayunos? | ✅ | ✅ | ✅ | ✅ |
| q04 | ¿En qué se diferencian RESIS y COLES? | ❌ | ❌ | ❌ | ❌ |
| q05 | ¿Cuántos voluntarios tiene DNI? | ✅ | ✅ | ✅ | ✅ |
| q06 | ¿Dónde es el punto de encuentro? | ✅ | ✅ | ✅ | ✅ |
| q07 | ¿Qué proyectos tiene DNI? | ✅ | ✅ | ✅ | ✅ |
| q08 | ¿Cuánto cuesta el alquiler? (fuera ámbito) | ✅ | ✅ | ✅ | ✅ |
| q09 | ¿Cómo contacto con DNI? | ✅ | ✅ | ✅ | ✅ |
| q10 | ¿Qué es el refuerzo escolar? | ✅ | ✅ | ✅ | ❌ |
| q11 | ¿Puedo apuntarme si soy menor? | ❌ | ❌ | ✅ | ❌ |
| q12 | ¿Cuándo se fundó DNI? | ✅ | ❌ | ✅ | ✅ |
| **Aciertos** | | **10/12** | **8/12** | **11/12** | **9/12** |

---

## Métricas de rendimiento (medias sobre las 12 preguntas)

| Modelo | Servidor | Latencia media (s) | Tokens/s medio | Tokens salida medios |
|--------|----------|--------------------|---------------|----------------------|
| qwen2.5:3b | ollama_local | 27.20 | 11.69 | 57.5 |
| llama3.2:3b | ollama_local | 24.96 | 10.47 | 54.1 |
| gemma3:27b | poligpt | 1.97 | 37.45 | 72.0 |
| llama3.3:70b | poligpt | 3.76 | 9.52 | 63.7 |

---

## Interpretación de resultados

El hallazgo más relevante del benchmark es la diferencia extrema en latencia entre los modelos locales y los de PoliGPT. qwen2.5:3b y llama3.2:3b tardan entre 15 y 43 segundos por pregunta ejecutándose en CPU pura, mientras que gemma3:27b en PoliGPT responde en menos de 3 segundos de media a pesar de ser un modelo casi diez veces mayor en parámetros. Esto refleja la diferencia entre inferencia en CPU de consumo y aceleración con hardware especializado en servidor.

En cuanto a calidad, gemma3:27b es el modelo con mejor rendimiento general (11/12 aciertos) y también el más rápido en términos de latencia real. llama3.3:70b, pese a ser el modelo más grande, no supera a gemma3:27b en calidad (9/12) y es más lento, lo que sugiere que el tamaño del modelo no es el único determinante de la calidad en tareas RAG sobre corpus pequeños.

La pregunta q04 ("¿En qué se diferencian RESIS y COLES?") fue fallada por los cuatro modelos. Esto no es un fallo del modelo sino del retrieval: los chunks recuperados para esa pregunta no contienen información comparativa directa entre ambos proyectos, sino información por separado de cada uno. Es un límite del sistema de recuperación top-k semántico que no está diseñado para síntesis comparativa cuando la información está dispersa en documentos distintos.

La pregunta q11 ("¿Puedo apuntarme si soy menor de edad?") fue respondida correctamente solo por gemma3:27b, que encontró la información en el corpus. Los modelos más pequeños rechazaron la pregunta incorrectamente, lo que indica menor capacidad de razonamiento sobre el contexto recuperado.

**Modelo elegido para producción: gemma3:27b (PoliGPT).** Justificación: mejor tasa de aciertos (11/12), latencia muy baja (1.97s media), y buena capacidad para detectar contradicciones entre documentos y sintetizar información de múltiples fuentes. La dependencia de VPN es el único inconveniente operativo; para entornos sin acceso a PoliGPT, qwen2.5:3b es la mejor alternativa local.
