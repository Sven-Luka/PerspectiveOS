import streamlit as st

try:
    from .core.config import AID_VISIBILITY_OPTIONS, FORMAT_OPTIONS, IMAGE_TYPES, TARGET_EMOTIONS, TOPICS
    from .core.knowledge import load_repository_knowledge
    from .production import ProductionFolderPipeline, ProductionRequest
except ImportError:
    from core.config import AID_VISIBILITY_OPTIONS, FORMAT_OPTIONS, IMAGE_TYPES, TARGET_EMOTIONS, TOPICS
    from core.knowledge import load_repository_knowledge
    from production import ProductionFolderPipeline, ProductionRequest


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
    location = st.text_input("Location")
    outfit = st.text_input("Outfit")
    aid_visibility = st.selectbox("Aid visibility", AID_VISIBILITY_OPTIONS, index=3)
    metaphor = st.text_input("Metaphor")
    format_name = st.selectbox("Format", FORMAT_OPTIONS)

    submitted = st.form_submit_button("Generate Brief")

if submitted:
    request = ProductionRequest(
        topic=topic,
        target_emotion=target_emotion,
        image_type=image_type,
        location=location,
        outfit=outfit,
        aid_visibility=aid_visibility,
        metaphor=metaphor,
        format_name=format_name,
    )
    production_folder = ProductionFolderPipeline(knowledge).create(request)
    brief = production_folder.files["brief.md"]

    st.success(f"Production folder generated: {production_folder.folder_name}")
    st.markdown(f"`{production_folder.relative_path}`")
    st.download_button(
        "Download Brief",
        data=brief,
        file_name="brief.md",
        mime="text/markdown",
    )
    st.markdown("### Generated Files")
    for file_name in production_folder.files:
        st.write(f"- {file_name}")
    st.markdown("### Preview")
    st.markdown(brief)
