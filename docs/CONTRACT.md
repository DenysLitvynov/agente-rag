# Contrato de interfaz

Especificación operativa del contrato del enunciado §9. **Si esto se rompe,
el corrector no puede evaluar y la nota es 0** (enunciado §9.1).

## Opción A — módulo Python (esta es la que usa este repo)

`consultar.py` debe exponer en la raíz del repositorio:

```python
def consultar(pregunta: str,
              conversation_id: str | None = None) -> dict:
    ...
```

Y la salida debe tener exactamente estas claves (algunas opcionales):

```json
{
  "respuesta": "string — texto de la respuesta",
  "fuentes": ["lista", "de", "nombres", "de", "archivo"],
  "chunks": [
    {"source": "1_primero.txt", "text": "...", "score": 0.84}
  ],
  "metricas": {
    "prompt_tokens": 612,
    "output_tokens": 45,
    "tokens_per_sec": 38.2,
    "latencia_s": 1.7,
    "modelo": "gemma2:27b"
  },
  "trazas": null
}
```

| Clave | Tipo | Banda | Notas |
|---|---|---|---|
| `respuesta` | `str` | 5 | No vacía. Si la pregunta es fuera de ámbito, contiene literalmente "No tengo esa información en mis fuentes". |
| `fuentes` | `list[str]` | 6 | Nombres de archivo del corpus (sin ruta). Únicos, en orden de aparición. |
| `chunks` | `list[dict]` o `null` | 7 | Cada chunk con `source`, `text`, `score`. |
| `metricas` | `dict` o `null` | 7 | 4 campos mínimos: `prompt_tokens`, `output_tokens`, `tokens_per_sec`, `latencia_s`. |
| `trazas` | `list[dict]` o `null` | opcional | No usado en este repo. Reservado para banda 8+ si queréis dejar log de RAGAs. |

## Opción B — endpoint HTTP

`api.py` expone `POST /query` con cuerpo:

```json
{ "pregunta": "...", "conversation_id": "...", "k": 5 }
```

y devuelve el mismo JSON que la opción A.

Si elegís esta opción, en `features.json`:

```json
{
  "interfaz": "endpoint_http",
  "endpoint_http": "http://127.0.0.1:8000/query"
}
```

## Cómo el corrector verifica el contrato (resumen)

1. Abre `features.json`. Si no es JSON válido o no es un objeto → entrega
   inválida.
2. Mira `interfaz`. Si `modulo_python`, importa `consultar.consultar`. Si
   `endpoint_http`, hace `POST` a la URL declarada.
3. Para cada pregunta del set oficial (confidencial):
   - Llama a la función / endpoint.
   - Comprueba que la salida es `dict` y tiene al menos `respuesta` y `fuentes`.
   - Verifica que la frase de rechazo aparece literalmente cuando toca.
   - Si declaráis banda 7, verifica que `chunks` y `metricas` son no-nulos.

## Errores frecuentes que invalidan la entrega

- `consultar.py` en `src/` en vez de en la raíz.
- Renombrar la función a `query`, `responder`, `chat`, ...
- Devolver una lista en vez de un dict.
- `features.json` con typo en `bandas_declaradas` (`banda_5` vs `banda5_pipeline_no_inventa`).
- Importar el módulo provoca side-effects pesados (cargar el modelo entero):
  el corrector tiene timeout. Cargad el índice y los modelos **dentro** de
  la función, no al importar.
