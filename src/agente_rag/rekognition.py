"""Extra AWS Rekognition: OCR de una imagen + verificación contra el corpus.

Flujo (integración, no OCR suelto):
    imagen --> Rekognition DetectText (OCR) --> texto detectado
           --> retrieve() recupera los chunks oficiales relevantes
           --> el LLM dictamina si el texto de la imagen COINCIDE / CONTRADICE
               / NO HAY INFORMACIÓN en el corpus, citando fuentes.

Reutiliza el mismo retriever y generador del agente, de modo que el extra está
realmente enganchado al pipeline RAG y no es una llamada desconectada.
"""

from __future__ import annotations

import os

import boto3

from .config import SETTINGS  # noqa: F401  (al importarse, ejecuta load_dotenv())
from .generator import generate
from .retriever import retrieve

# Rekognition síncrono admite imágenes de hasta 5 MB enviadas como bytes.
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def _rekognition_client():
    """Cliente boto3 de Rekognition. Las credenciales las toma boto3 del entorno
    (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY, cargadas desde .env)."""
    region = os.getenv("AWS_REGION", "eu-west-1")
    return boto3.client("rekognition", region_name=region)


def extraer_texto(image_bytes: bytes) -> str:
    """Devuelve el texto detectado en la imagen (solo líneas), unido por saltos."""
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError(
            "La imagen supera los 5 MB que admite Rekognition de forma síncrona. "
            "Redúcela o redimensiónala antes de enviarla."
        )
    client = _rekognition_client()
    resp = client.detect_text(Image={"Bytes": image_bytes})
    lineas = [
        d["DetectedText"]
        for d in resp.get("TextDetections", [])
        if d.get("Type") == "LINE"
    ]
    return "\n".join(lineas)


VERIFY_TEMPLATE = """Eres el verificador oficial de la asociación DNI (Damos Nuestra Ilusión) Valencia.

Te doy el CONTENIDO OFICIAL (extraído del corpus de DNI) y un TEXTO DETECTADO en una imagen subida por el usuario (un cartel, un horario impreso, un post...). Tu tarea es decir si el texto de la imagen es coherente con la información oficial.

REGLAS — obligatorias:
1. Usa ÚNICAMENTE el contenido oficial de abajo. No uses conocimiento externo.
2. Empieza tu respuesta con una de estas tres etiquetas:
   - "COINCIDE:" si lo que dice la imagen concuerda con el corpus.
   - "CONTRADICE:" si la imagen afirma algo que el corpus desmiente (p. ej. una hora o un lugar distinto).
   - "SIN INFORMACIÓN:" si el corpus no contiene datos para verificar la imagen.
3. Justifica en una o dos frases citando entre paréntesis los archivos fuente.
4. No deduzcas ni inventes nada que no esté en el contenido oficial.

CONTENIDO OFICIAL:
{context}

TEXTO DETECTADO EN LA IMAGEN:
{texto_imagen}

VEREDICTO:"""


def verificar_imagen(image_bytes: bytes, *, k: int = 10) -> dict:
    """OCR de la imagen + verificación contra el corpus.

    Devuelve un dict con: ``texto_imagen`` (lo detectado por OCR), ``veredicto``
    (respuesta del agente), ``fuentes``, ``chunks`` y ``metricas``.
    """
    texto_imagen = extraer_texto(image_bytes)

    if not texto_imagen.strip():
        return {
            "texto_imagen": "",
            "veredicto": "No se ha detectado texto en la imagen.",
            "fuentes": [],
            "chunks": [],
            "metricas": None,
        }

    retrieved = retrieve(texto_imagen, k=k)
    context = "\n\n".join(f"[{c.source}]\n{c.text}" for c in retrieved)
    prompt = VERIFY_TEMPLATE.format(context=context, texto_imagen=texto_imagen)
    gen = generate(prompt)

    return {
        "texto_imagen": texto_imagen,
        "veredicto": gen.text.strip(),
        "fuentes": _unique_preserving_order(c.source for c in retrieved),
        "chunks": [
            {"source": c.source, "text": c.text, "score": c.score} for c in retrieved
        ],
        "metricas": {
            "prompt_tokens": gen.prompt_tokens,
            "output_tokens": gen.output_tokens,
            "tokens_per_sec": gen.tokens_per_sec,
            "latencia_s": gen.latency_s,
            "modelo": gen.model,
        },
    }


def _unique_preserving_order(items) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out
