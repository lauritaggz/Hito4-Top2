"""Interfaz Streamlit del Asistente RAG de Soporte Técnico."""

import streamlit as st

import config
from rag import EmptyIndexError, OllamaError, RAGError, is_index_ready, query

st.set_page_config(
    page_title="Asistente RAG de Soporte Técnico",
    page_icon="🛠️",
    layout="wide",
)

st.title("Asistente RAG de Soporte Técnico")
st.write(
    "Este asistente responde usando documentos locales indexados en una base vectorial."
)

# Barra lateral
with st.sidebar:
    st.header("Configuración")
    st.markdown(f"**Modelo LLM:** `{config.OLLAMA_LLM_MODEL}`")
    st.markdown(f"**Modelo embeddings:** `{config.OLLAMA_EMBED_MODEL}`")
    st.markdown(f"**Chunks por consulta:** {config.TOP_K}")

    st.divider()
    st.subheader("Instrucciones rápidas")
    st.code(
        "pip install -r requirements.txt\n"
        "ollama pull nomic-embed-text\n"
        "python ingest.py\n"
        "streamlit run app.py",
        language="bash",
    )

ready, status_message = is_index_ready()

if not ready:
    st.warning("Primero ejecuta: python ingest.py")
    if status_message:
        st.caption(status_message)
    st.stop()

user_question = st.text_area(
    "Escribe tu pregunta:",
    placeholder="Ejemplo: ¿Cómo crear una imagen Docker?",
    height=100,
)

if st.button("Preguntar", type="primary"):
    if not user_question.strip():
        st.error("Por favor, escribe una pregunta.")
    else:
        with st.spinner(
            "Buscando información y generando respuesta... "
            "(qwen3:4b puede tardar 1-3 min la primera vez)"
        ):
            try:
                result = query(user_question.strip())

                st.subheader("Respuesta")
                st.markdown(result.answer)

                st.subheader("Fuentes utilizadas")
                if result.sources:
                    for source in result.sources:
                        st.markdown(f"- `{source}`")
                else:
                    st.markdown("_Sin fuentes disponibles._")

                with st.expander("Fragmentos recuperados"):
                    if result.fragments:
                        for i, frag in enumerate(result.fragments, start=1):
                            page_info = (
                                f" | Página: {frag['page']}"
                                if frag.get("page")
                                else ""
                            )
                            st.markdown(
                                f"**Fragmento {i}** — `{frag['source']}`"
                                f" (chunk {frag.get('chunk', '?')}{page_info})"
                            )
                            st.text(frag["text"])
                            st.divider()
                    else:
                        st.write("No se recuperaron fragmentos.")

            except OllamaError as exc:
                st.error(str(exc))
                st.info(
                    "Verifica que Ollama esté en ejecución: "
                    "`ollama serve` o el servicio del sistema."
                )
            except EmptyIndexError:
                st.warning("Primero ejecuta: python ingest.py")
            except RAGError as exc:
                st.error(str(exc))
