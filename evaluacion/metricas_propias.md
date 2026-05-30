# Métricas Propias de Evaluación

En esta sección detallamos las dos métricas personalizadas diseñadas para evaluar aspectos críticos del Agente RAG para DNI Valencia, complementando las métricas estándar de RAGAs.

---

## 1. Source Citation Accuracy

Mide si la respuesta contiene referencias o citas válidas a los documentos del corpus oficial.

### Definición y Cálculo
Se verifica si el campo `fuentes` del resultado de la consulta no está vacío y contiene documentos existentes en el corpus.
* **0.0:** No se incluye ninguna cita de fuente.
* **1.0:** Se citan correctamente las fuentes oficiales de información.

### Justificación
Para la asociación DNI Valencia, es de vital importancia que el asistente de voluntariado no invente respuestas y que cada dato (direcciones, horarios, contactos) esté directamente respaldado por un documento oficial. Esta métrica asegura que el pipeline recupera y etiqueta correctamente la procedencia de la información.

### Valor obtenido
* **Valor Promedio:** `1.00` (100%)
* *Desglose:* 1.0 en las 5 preguntas evaluadas, demostrando un comportamiento impecable en la atribución de fuentes.

---

## 2. Contradiction Handling Score

Mide si la respuesta detecta, maneja y expone de forma explícita las posibles contradicciones o matices entre los documentos recuperados.

### Definición y Cálculo
Analiza el texto de la respuesta en busca de términos de comparación y atribución (por ejemplo: "según", "archivo", "por otro lado", "sin embargo") cuando se le presentan documentos contradictorios en el contexto.
* **Rango:** `0.0` a `1.0` basado en la densidad de términos explicativos sobre la fuente de contradicción.

### Justificación
El corpus de una ONG suele actualizarse de manera fragmentada (por ejemplo, documentos antiguos conviviendo con nuevos sobre el mismo tema). Si el sistema recupera dos directrices contradictorias, no debe elegir una al azar; debe advertir al voluntario sobre la inconsistencia. Esta métrica evalúa esa robustez y transparencia.

### Valor obtenido
* **Valor Promedio:** `0.10` (10%)
* *Desglose:*
  * q01-q03 y q05: 0.0 (no se requería ni se expuso contradicción).
  * q04 ("¿Cómo puedo unirme a DNI?"): 0.5 (detectó y expuso la procedencia y matices del documento `09_como_participar.txt`).