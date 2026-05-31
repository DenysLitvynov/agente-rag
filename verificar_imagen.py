"""Prueba rápida del extra de Rekognition desde la terminal.

Uso:
    python verificar_imagen.py ruta/a/la/imagen.jpg

Sirve para comprobar de forma aislada que las credenciales de AWS funcionan y
que el OCR + verificación contra el corpus van bien, antes de usarlo en el
frontend.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from agente_rag.rekognition import verificar_imagen  # noqa: E402


def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Uso: python verificar_imagen.py <ruta_imagen>")
        return 1

    ruta = Path(argv[1])
    if not ruta.exists():
        print(f"No existe el archivo: {ruta}")
        return 1

    try:
        resultado = verificar_imagen(ruta.read_bytes())
    except Exception as exc:  # noqa: BLE001
        print("Error al verificar la imagen:")
        print(f"  {type(exc).__name__}: {exc}")
        return 1

    print("=== TEXTO DETECTADO EN LA IMAGEN ===")
    print(resultado["texto_imagen"] or "(no se detectó texto)")
    print()
    print("=== VEREDICTO DEL AGENTE ===")
    print(resultado["veredicto"])
    print()
    fuentes = resultado.get("fuentes") or []
    print("Fuentes:", ", ".join(fuentes) if fuentes else "—")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
