"""Frontend Streamlit del Asistente DNI (extras: frontend + AWS Rekognition).

Dos modos, seleccionables en la barra lateral:
  - Preguntar: chat que consume el contrato oficial ``consultar()``.
  - Verificar imagen: sube una foto (un cartel, un horario) y el agente comprueba,
    vía Rekognition (OCR) + el corpus, si su contenido coincide con la
    información oficial de DNI.

El frontend no reimplementa nada del dominio: importa ``consultar()`` y el módulo
``rekognition`` y se limita a presentar los resultados.

Lanzar desde la raíz del repositorio:
    streamlit run frontend/app.py
"""

from __future__ import annotations

import html
import sys
import uuid
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
      <p class="dni-sub">Pregúntame sobre la asociación <strong>Damos Nuestra Ilusión</strong> (Valencia),
      o verifica una imagen contra la información oficial. Cito siempre las fuentes.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ------------------------------- Estado de sesión ---------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conv_id" not in st.session_state:
    st.session_state.conv_id = str(uuid.uuid4())
if "pending" not in st.session_state:
    st.session_state.pending = None


# ------------------------------- Utilidades ---------------------------------
def _friendly_error(exc) -> str:
    s = str(exc).lower()
    if any(t in s for t in ("connection", "max retries", "refused")):
        return "No consigo conectar con Ollama. Comprueba que está en marcha (`ollama serve`)."
    if "404" in s and "generate" in s:
        return "Ollama responde pero no encuentra el modelo. Revisa `LLM_MODEL` en tu `.env` y `ollama list`."
    if any(t in s for t in ("collection", "does not exist", "get_collection")):
        return "No encuentro el índice vectorial. Ejecuta `python scripts/build_index.py`."
    return f"Error al consultar el agente:\n\n```\n{exc}\n```"


def _friendly_error_aws(exc) -> str:
    s = str(exc).lower()
    name = type(exc).__name__.lower()
    if "nocredentials" in name or "unable to locate credentials" in s:
        return "No encuentro las credenciales de AWS. Revisa `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY` en tu `.env`."
    if any(t in s for t in ("invalidclienttoken", "signaturedoesnotmatch", "invalidsignature", "unrecognizedclient")):
        return "Las credenciales de AWS no son válidas. Revisa que la clave y el secret estén bien copiados en el `.env`."
    if "accessdenied" in s:
        return "Tu usuario de AWS no tiene permiso para Rekognition. Asígnale la política `AmazonRekognitionReadOnlyAccess`."
    if isinstance(exc, ValueError):
        return str(exc)
    if "modulenotfound" in name or ("boto3" in s and "no module" in s):
        return "Falta `boto3`. Instálalo con `pip install boto3`."
    if any(t in s for t in ("endpoint", "could not connect", "region")):
        return "Problema de conexión o región con AWS. Revisa `AWS_REGION` (usa `eu-west-1`) y tu conexión."
    return f"Error al verificar la imagen:\n\n```\n{exc}\n```"


def render_chips(fuentes) -> None:
    if fuentes:
        chips = " ".join(f'<span class="chip">📄 {html.escape(str(f))}</span>' for f in fuentes)
        st.markdown(f'<div class="chips-row">{chips}</div>', unsafe_allow_html=True)


def render_chunks_metrics(chunks, metricas) -> None:
    with st.expander("🔍 Ver chunks recuperados y métricas"):
        if chunks:
            for c in chunks:
                src = html.escape(str(c.get("source", "—")))
                score = c.get("score", "—")
                text = html.escape(str(c.get("text", "")))
                st.markdown(
                    f'<div class="chunk-card"><div class="chunk-head">'
                    f'<span class="chunk-src">{src}</span>'
                    f'<span class="score-pill">score {score}</span></div>'
                    f'<div class="chunk-text">{text}</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No se recuperaron chunks.")
        if metricas:
            st.markdown("**Métricas de generación**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Latencia", f"{metricas.get('latencia_s', '?')} s")
            c2.metric("Tokens/s", metricas.get("tokens_per_sec", "?"))
            c3.metric("Modelo", metricas.get("modelo", "?"))
            st.caption(
                f"Tokens de entrada: {metricas.get('prompt_tokens', '?')} · "
                f"de salida: {metricas.get('output_tokens', '?')}"
            )


def render_answer(result: dict) -> None:
    st.markdown(result.get("respuesta", ""))
    render_chips(result.get("fuentes") or [])
    render_chunks_metrics(result.get("chunks") or [], result.get("metricas") or {})


def render_verdict(veredicto: str) -> None:
    up = veredicto.strip().upper()
    if up.startswith("COINCIDE"):
        st.success(veredicto)
    elif up.startswith("CONTRADICE"):
        st.error(veredicto)
    elif up.startswith("SIN INFORMACI"):
        st.warning(veredicto)
    else:
        st.info(veredicto)


EJEMPLOS = [
    "¿Qué es DNI?",
    "¿Cómo me apunto a los desayunos solidarios?",
    "¿En qué se diferencian RESIS y COLES?",
    "¿Cuánto cuesta el alquiler en Valencia?",
]


# ------------------------------- Barra lateral ------------------------------
with st.sidebar:
    st.markdown("### Modo")
    modo = st.radio(
        "Modo", ["💬 Preguntar", "🖼️ Verificar imagen"], label_visibility="collapsed"
    )

    st.divider()
    st.markdown("### ⚙️ Configuración activa")
    st.markdown(f"- **LLM:** `{SETTINGS.llm_model}`")
    st.markdown(f"- **Embeddings:** `{SETTINGS.embed_model}`")
    st.markdown(f"- **Colección:** `{SETTINGS.collection_name}`")
    st.markdown(f"- **Ollama:** `{SETTINGS.ollama_url}`")

    if modo == "💬 Preguntar":
        st.divider()
        st.markdown("### 💡 Preguntas de ejemplo")
        for ej in EJEMPLOS:
            if st.button(ej, use_container_width=True, key=f"ej_{ej}"):
                st.session_state.pending = ej
        st.divider()
        if st.button("🗑️ Limpiar conversación", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conv_id = str(uuid.uuid4())
            st.rerun()


# ------------------------------- Modo: Preguntar ----------------------------
if modo == "💬 Preguntar":
    for msg in st.session_state.messages:
        avatar = "🧑" if msg["role"] == "user" else "🤝"
        with st.chat_message(msg["role"], avatar=avatar):
            if msg["role"] == "user":
                st.markdown(msg["content"])
            else:
                render_answer(msg["result"])

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
                except Exception as exc:  # noqa: BLE001
                    result, error = None, exc
            if error is not None:
                st.error(_friendly_error(error))
            else:
                render_answer(result)
                st.session_state.messages.append({"role": "assistant", "result": result})


# --------------------------- Modo: Verificar imagen -------------------------
else:
    st.markdown("#### Verificar una imagen contra el corpus oficial")
    st.caption(
        "Sube una foto (un cartel, un horario impreso, un post…). El agente extrae el "
        "texto con AWS Rekognition y comprueba si coincide con la información oficial de DNI."
    )
    uploaded = st.file_uploader("Imagen", type=["png", "jpg", "jpeg"])

    if uploaded is not None:
        st.image(uploaded, width=380)
        if st.button("Verificar contra el corpus", type="primary"):
            with st.spinner("Leyendo la imagen (OCR) y verificando contra el corpus…"):
                try:
                    from agente_rag.rekognition import verificar_imagen

                    result = verificar_imagen(uploaded.getvalue())
                    error = None
                except Exception as exc:  # noqa: BLE001
                    result, error = None, exc

            if error is not None:
                st.error(_friendly_error_aws(error))
            else:
                st.markdown("**Texto detectado en la imagen:**")
                st.code(result["texto_imagen"] or "(no se detectó texto)")
                st.markdown("**Veredicto del agente:**")
                render_verdict(result["veredicto"])
                render_chips(result.get("fuentes") or [])
                render_chunks_metrics(result.get("chunks") or [], result.get("metricas") or {})
