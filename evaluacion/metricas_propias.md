# Métricas Propias de Evaluación

En esta sección detallamos las dos métricas personalizadas diseñadas para evaluar aspectos críticos del Agente RAG para DNI Valencia, complementando las métricas estándar de RAGAs. Ambas métricas se centran en requisitos operativos reales de la asociación: la trazabilidad de la información y la gestión de inconsistencias documentales.

---

## 1. Source Citation Accuracy (Precisión de Citación de Fuentes)

Mide si cada respuesta generada por el sistema RAG incluye una referencia verificable a los documentos oficiales del corpus de DNI Valencia de los que extrajo la información.

### Definición y Cálculo
Se inspecciona el campo `fuentes` del diccionario de salida del pipeline (`answer()`). La métrica vale:
* **0.0:** La respuesta no incluye ninguna referencia a documentos del corpus (el campo `fuentes` está vacío).
* **1.0:** La respuesta incluye al menos una referencia válida a un fichero `.txt` del corpus oficial.

### Justificación (pertinencia al dominio DNI)
Los voluntarios de DNI Valencia coordinan actividades presenciales críticas: reparto de alimentos a personas sin hogar, refuerzo escolar a menores y visitas a residencias de ancianos. Si el chatbot proporciona una dirección, un horario o un teléfono de contacto **sin indicar de qué documento oficial proviene**, el voluntario no tiene forma de verificar si ese dato está actualizado o si es una alucinación del modelo. En un contexto donde un error (por ejemplo, un punto de encuentro incorrecto a las 7:30 de la mañana) puede dejar a personas vulnerables sin atender, la trazabilidad documental no es un lujo sino una necesidad operativa. Esta métrica garantiza que el pipeline siempre etiqueta el origen de cada respuesta.

### Valor obtenido
* **Valor Promedio:** `1.00` (100%)
* *Desglose:* 1.0 en las 5 preguntas evaluadas — el sistema cita correctamente las fuentes en todas las respuestas.

---

## 2. Contradiction Handling Score (Puntuación de Gestión de Contradicciones)

Mide la capacidad del sistema para detectar y exponer de forma transparente las posibles contradicciones o matices entre los documentos recuperados del corpus, en lugar de elegir silenciosamente una versión.

### Definición y Cálculo
Se analiza el texto de la respuesta generada buscando indicadores lingüísticos de atribución explícita a fuentes concretas. Se contabiliza la presencia de los siguientes marcadores:
* `"según"` — indica que el sistema atribuye información a una fuente específica.
* `"archivo"` — indica que el sistema referencia un documento concreto del corpus.

La puntuación se calcula como la proporción de marcadores encontrados sobre el total (2), resultando en un rango continuo de `0.0` a `1.0`.

### Justificación (pertinencia al dominio DNI)
El corpus de DNI Valencia contiene 16 documentos que fueron redactados en diferentes momentos y por diferentes miembros de la asociación. Esto genera inconsistencias naturales: por ejemplo, un documento puede indicar que el refuerzo escolar es en el CEIP Antonio Ferrandis mientras otro menciona una "biblioteca tutorizada" sin especificar ubicación. Si el retriever recupera ambos chunks, el sistema no debe elegir una versión al azar ni fusionarlas silenciosamente. Debe advertir al voluntario: *"según [documento X] la ubicación es A, pero según [documento Y] se menciona B"*. Esta transparencia es especialmente importante en una ONG donde las instrucciones cambian con frecuencia y los voluntarios nuevos necesitan saber cuál es la fuente más fiable. La métrica evalúa si el sistema presenta esta transparencia activamente.

### Valor obtenido
* **Valor Promedio:** `0.10` (10%)
* *Desglose:*
  * q01-q03 y q05: 0.0 — preguntas factuales directas donde no había contradicción entre fuentes, por lo que la ausencia de marcadores es el comportamiento esperado.
  * q04 ("¿Cómo puedo unirme a DNI?"): 0.5 — el sistema detectó y expuso la procedencia de la información citando explícitamente el documento `09_como_participar.txt` con el marcador "según", demostrando capacidad de atribución activa.
