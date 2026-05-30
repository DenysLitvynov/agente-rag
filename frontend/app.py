"""Frontend Streamlit del Asistente DNI (extra: frontend, +1.5).

Este frontend NO reimplementa nada del dominio: importa la función del contrato
oficial ``consultar()`` (enunciado §9, opción A) desde la raíz del repositorio
—la misma que llama el corrector— y se limita a presentar el resultado:

    - la respuesta del agente,
    - las FUENTES citadas (banda 6),
    - los CHUNKS recuperados con su score (banda 7),
    - las MÉTRICAS de generación (latencia, tokens/s, modelo).

Así queda claro que el agente está realmente conectado y que el frontend es
funcional, no cosmético.

Lanzar SIEMPRE desde la raíz del repositorio:

    streamlit run frontend/app.py
"""

from __future__ import annotations

import html
import sys
import uuid
from pathlib import Path

import streamlit as st

# --- Hacemos importable la raíz del repo (donde vive consultar.py) ----------
# El frontend está en frontend/, así que subimos un nivel para alcanzar la raíz.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# consultar.py ya añade src/ al path al importarse, así que después de esta
# línea el paquete agente_rag también es importable.
from consultar import consultar  # noqa: E402  (contrato oficial)
from agente_rag.config import SETTINGS  # noqa: E402  (solo para mostrar config)


# ----------------------------- Página y estilos -----------------------------
st.set_page_config(
    page_title="Asistente DNI · Valencia",
    page_icon="🤝",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Spline+Sans:wght@400;500;600&display=swap');

    .stApp { background: #fbf6ee; }
    .stApp, .stApp p, .stApp li, .stApp label {
        font-family: 'Spline Sans', system-ui, sans-serif;
    }
    h1, h2, h3 { font-family: 'Fraunces', Georgia, serif !important; letter-spacing: -0.01em; }

    .dni-header { text-align: center; padding: 0.4rem 0 0.6rem; }
    .dni-lema {
        display: inline-block; font-weight: 600; letter-spacing: 0.18em;
        font-size: 0.72rem; color: #2f7d6e; background: #e7f0ed;
        padding: 0.3rem 0.75rem; border-radius: 999px;
    }
    .dni-header h1 { font-size: 2.5rem; margin: 0.5rem 0 0.2rem; color: #2a2421; }
    .dni-sub { color: #6f655b; max-width: 34rem; margin: 0 auto; font-size: 0.95rem; line-height: 1.5; }

    .chips-row { margin-top: 0.6rem; display: flex; flex-wrap: wrap; gap: 0.4rem; }
    .chip {
        background: #ffffff; border: 1px solid #ecd9c9; color: #b24a26;
        font-size: 0.78rem; padding: 0.22rem 0.62rem; border-radius: 999px; font-weight: 500;
    }

    .chunk-card {
        background: #ffffff; border: 1px solid #efe3d3; border-radius: 12px;
        padding: 0.7rem 0.85rem; margin-bottom: 0.6rem;
    }
    .chunk-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem; gap: 0.5rem; }
    .chunk-src { font-weight: 600; font-size: 0.82rem; color: #2a2421; }
    .score-pill {
        font-size: 0.72rem; color: #2f7d6e; background: #e7f0ed;
        padding: 0.12rem 0.5rem; border-radius: 999px; white-space: nowrap;
    }
    .chunk-text { font-size: 0.84rem; color: #5a5149; white-space: pre-wrap; line-height: 1.45; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="dni-header">
      <div class="dni-lema">PARA · MIRA · AYUDA</div>
      <h1>Asistente DNI</h1>
      <p class="dni-sub">Pregúntame sobre la asociación <strong>Damos Nuestra Ilusión</strong> (Valencia).
      Respondo únicamente con la información de los documentos oficiales y te cito las fuentes.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ------------------------------- Estado de sesión ---------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []  # [{role, content?|result?}]
if "conv_id" not in st.session_state:
    st.session_state.conv_id = str(uuid.uuid4())
if "pending" not in st.session_state:
    st.session_state.pending = None


# ------------------------------- Utilidades ---------------------------------
def _friendly_error(exc: Exception) -> str:
    """Traduce los fallos típicos a un mensaje accionable para el usuario."""
    s = str(exc).lower()
    if any(t in s for t in ("connection", "max retries", "refused", "connectionerror")):
        return (
            "No consigo conectar con Ollama. Comprueba que está en marcha "
            "(`ollama serve`) y vuelve a intentarlo."
        )
    if "404" in s and "generate" in s:
        return (
            "Ollama responde pero no encuentra el modelo. Revisa `LLM_MODEL` en tu "
            "`.env` y que esté descargado (`ollama list`)."
        )
    if any(t in s for t in ("collection", "does not exist", "get_collection")):
        return (
            "No encuentro el índice vectorial. Ejecuta primero "
            "`python scripts/build_index.py` para construir la colección."
        )
    return f"Ha ocurrido un error al consultar el agente:\n\n```\n{exc}\n```"


def render_answer(result: dict) -> None:
    """Pinta una respuesta del agente: texto + fuentes + chunks + métricas."""
    st.markdown(result.get("respuesta", ""))

    fuentes = result.get("fuentes") or []
    if fuentes:
        chips = " ".join(f'<span class="chip">📄 {html.escape(str(f))}</span>' for f in fuentes)
        st.markdown(f'<div class="chips-row">{chips}</div>', unsafe_allow_html=True)

    with st.expander("🔍 Ver chunks recuperados y métricas"):
        chunks = result.get("chunks") or []
        if chunks:
            for c in chunks:
                src = html.escape(str(c.get("source", "—")))
                score = c.get("score", "—")
                text = html.escape(str(c.get("text", "")))
                st.markdown(
                    f'<div class="chunk-card">'
                    f'<div class="chunk-head">'
                    f'<span class="chunk-src">{src}</span>'
                    f'<span class="score-pill">score {score}</span>'
                    f"</div>"
                    f'<div class="chunk-text">{text}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No se recuperaron chunks para esta pregunta.")

        m = result.get("metricas") or {}
        if m:
            st.markdown("**Métricas de generación**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Latencia", f"{m.get('latencia_s', '?')} s")
            c2.metric("Tokens/s", m.get("tokens_per_sec", "?"))
            c3.metric("Modelo", m.get("modelo", "?"))
            st.caption(
                f"Tokens de entrada: {m.get('prompt_tokens', '?')} · "
                f"de salida: {m.get('output_tokens', '?')}"
            )


# ------------------------------- Barra lateral ------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Configuración activa")
    st.caption("Lo que el agente está usando ahora mismo:")
    st.markdown(f"- **LLM:** `{SETTINGS.llm_model}`")
    st.markdown(f"- **Embeddings:** `{SETTINGS.embed_model}`")
    st.markdown(f"- **Colección:** `{SETTINGS.collection_name}`")
    st.markdown(f"- **Ollama:** `{SETTINGS.ollama_url}`")

    st.divider()
    st.markdown("### 💡 Preguntas de ejemplo")
    EJEMPLOS = [
        "¿Qué es DNI?",
        "¿Cómo me apunto a los desayunos solidarios?",
        "¿En qué se diferencian RESIS y COLES?",
        "¿Cuánto cuesta el alquiler en Valencia?",  # fuera de ámbito (debe rechazarla)
    ]
    for ej in EJEMPLOS:
        if st.button(ej, use_container_width=True, key=f"ej_{ej}"):
            st.session_state.pending = ej

    st.divider()
    if st.button("🗑️ Limpiar conversación", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conv_id = str(uuid.uuid4())
        st.rerun()


# ------------------------------- Historial ----------------------------------
for msg in st.session_state.messages:
    avatar = "🧑" if msg["role"] == "user" else "🤝"
    with st.chat_message(msg["role"], avatar=avatar):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            render_answer(msg["result"])


# ------------------------------- Entrada ------------------------------------
prompt = st.chat_input("Escribe tu pregunta sobre DNI…")
if st.session_state.pending and not prompt:
    prompt = st.session_state.pending
    st.session_state.pending = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤝"):
        with st.spinner("Buscando en el corpus y generando la respuesta… (en CPU puede tardar)"):
            try:
                result = consultar(prompt, conversation_id=st.session_state.conv_id)
                error = None
            except Exception as exc:  # noqa: BLE001  (queremos mostrar cualquier fallo)
                result, error = None, exc

        if error is not None:
            st.error(_friendly_error(error))
        else:
            render_answer(result)
            st.session_state.messages.append({"role": "assistant", "result": result})
