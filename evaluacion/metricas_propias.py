from __future__ import annotations


def source_citation_accuracy(answer: dict) -> float:
    """
    Comprueba si la respuesta tiene fuentes.
    """

    fuentes = answer.get("fuentes", [])

    if not fuentes:
        return 0.0

    return 1.0


def contradiction_handling_score(answer: dict) -> float:
    """
    Comprueba si el sistema detecta contradicciones.
    """

    respuesta = answer.get("respuesta", "").lower()

    claves = [
        "según",
        "archivo",
    ]

    encontrados = sum(1 for k in claves if k in respuesta)

    return encontrados / len(claves)