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

AID_VISIBILITY_OPTIONS = [
    "orthosis",
    "diaper",
    "both",
    "subtle",
    "none",
]

# Backward-compatible alias for earlier v0.3 imports.
AI_VISIBILITY_OPTIONS = AID_VISIBILITY_OPTIONS

FORMAT_OPTIONS = [
    "Feed 4:5",
    "Story 9:16",
    "Reel Cover",
]

REQUIRED_DOCUMENTS = list(ProjectSettings().required_knowledge_documents)
