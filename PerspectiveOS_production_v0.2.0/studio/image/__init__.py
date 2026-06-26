"""Asset registry and image-production services for Perspective Studio."""

from .asset_registry import AssetRecord, AssetRegistry
from .generator import GeneratedImage, ImageGenerationError, ImageGenerator
from .layout_composer import ComposedLayout, LayoutComposer, LayoutCompositionError, LayoutContent
from .prompt_contract import (
    ImagePromptContract,
    ImagePromptContractBuilder,
    missing_required_terms,
    render_image_prompt_contract,
)
from .reference_selector import ReferenceImage, ReferenceSelector
from .vision_review import VisionReviewer, VisualReview, VisualReviewFinding
from .visual_agent import VisualAgent, VisualAgentResult

__all__ = [
    "AssetRecord",
    "AssetRegistry",
    "GeneratedImage",
    "ImageGenerationError",
    "ImageGenerator",
    "ImagePromptContract",
    "ImagePromptContractBuilder",
    "ComposedLayout",
    "LayoutComposer",
    "LayoutCompositionError",
    "LayoutContent",
    "ReferenceImage",
    "ReferenceSelector",
    "VisionReviewer",
    "VisualReview",
    "VisualAgent",
    "VisualAgentResult",
    "VisualReviewFinding",
    "missing_required_terms",
    "render_image_prompt_contract",
]
