import streamlit as st

from core.config import IMAGE_TYPES, TARGET_EMOTIONS, TOPICS
from core.knowledge import load_repository_knowledge
from core.storage import save_brief
from creative.brief_generator import BriefGenerator


st.set_page_config(page_title="Perspective Studio", page_icon="PS", layout="centered")

knowledge = load_repository_knowledge()

with st.sidebar:
    st.header("Repository Knowledge")
    st.subheader("Loaded documents")
    if knowledge.loaded_documents:
        for document in knowledge.loaded_documents:
            st.write(f"- {document}")
    else:
        st.write("None")

    st.subheader("Missing documents")
    if knowledge.missing_documents:
        for document in knowledge.missing_documents:
            st.write(f"- {document}")
    else:
        st.write("None")

    st.subheader("Last refresh")
    st.write(knowledge.last_refresh)

st.title("Perspective Studio")
st.divider()

st.header("Create New Post")

with st.form("create_new_post"):
    topic = st.selectbox("Topic", TOPICS)
    target_emotion = st.selectbox("Target Emotion", TARGET_EMOTIONS)
    image_type = st.selectbox("Image Type", IMAGE_TYPES)

    submitted = st.form_submit_button("Generate Brief")

if submitted:
    brief = BriefGenerator(knowledge).generate(topic, target_emotion, image_type)
    output_path = save_brief(topic, brief)

    st.success(f"Brief generated: {output_path.name}")
    st.markdown(f"`{output_path}`")
    st.download_button(
        "Download Brief",
        data=brief,
        file_name=output_path.name,
        mime="text/markdown",
    )
    st.markdown("### Preview")
    st.markdown(brief)
