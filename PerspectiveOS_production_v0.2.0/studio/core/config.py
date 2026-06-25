from .settings import ProjectSettings


TOPICS = [
    "Anders gedacht",
    "Outfit",
    "Orthosis",
    "Incontinence",
    "Dating",
    "Humor",
    "Community",
]

TARGET_EMOTIONS = [
    "Smile",
    "Think",
    "Empower",
    "Surprise",
]

IMAGE_TYPES = [
    "Single Image",
    "Carousel",
    "Reel",
]

REQUIRED_DOCUMENTS = list(ProjectSettings().required_knowledge_documents)
