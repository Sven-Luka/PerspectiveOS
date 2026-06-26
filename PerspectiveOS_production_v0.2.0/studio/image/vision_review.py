import base64
import json
import os
import struct
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .prompt_contract import ImagePromptContract, missing_required_terms
from .reference_selector import ReferenceImage


EXPECTED_DIMENSIONS = {
    "Feed 4:5": (1024, 1536),
    "Story 9:16": (1024, 1536),
    "Reel Cover": (1024, 1024),
}


@dataclass(frozen=True)
class VisualReviewFinding:
    """One visual review finding for a generated image."""

    severity: str
    check: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "check": self.check,
            "message": self.message,
        }


@dataclass(frozen=True)
class VisualReview:
    """Deterministic visual review result and correction prompt."""

    status: str
    generated_at: str
    findings: list[VisualReviewFinding]
    correction_prompt: str

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "generated_at": self.generated_at,
            "findings": [finding.to_dict() for finding in self.findings],
            "correction_prompt": self.correction_prompt,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def to_markdown(self) -> str:
        lines = [
            "# Visual Review",
            "",
            f"Status: {self.status.upper()}",
            f"Generated at: {self.generated_at}",
            "",
            "## Findings",
        ]
        if not self.findings:
            lines.append("- No deterministic findings.")
        else:
            for finding in self.findings:
                lines.append(f"- [{finding.severity.upper()}] {finding.check}: {finding.message}")
        lines.extend(["", "## Correction Prompt", self.correction_prompt])
        return "\n".join(lines) + "\n"


class VisionReviewer:
    """Reviews generated image files against the image contract and selected references."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model or os.environ.get("OPENAI_VISION_REVIEW_MODEL", "gpt-5.5")

    def review(
        self,
        *,
        image_path: Path,
        prompt: str,
        format_name: str,
        contract: ImagePromptContract,
        references: list[ReferenceImage],
        carousel_source_count: int = 1,
    ) -> VisualReview:
        findings: list[VisualReviewFinding] = []
        findings.extend(self._image_file(image_path, format_name))
        findings.extend(self._prompt_contract(prompt, contract))
        findings.extend(self._references(references))
        findings.extend(self._carousel_sources(carousel_source_count))
        findings.extend(self._semantic_review(image_path, references))
        status = self._status(findings)
        return VisualReview(
            status=status,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            findings=findings,
            correction_prompt=self._correction_prompt(findings),
        )

    def _image_file(self, image_path: Path, format_name: str) -> list[VisualReviewFinding]:
        if not image_path.exists():
            return [VisualReviewFinding("fail", "image_file", f"Missing image file: {image_path}")]
        dimensions = _png_dimensions(image_path)
        if dimensions is None:
            return [
                VisualReviewFinding(
                    "warn",
                    "image_file",
                    "Could not read PNG dimensions. Confirm format manually.",
                )
            ]
        expected = EXPECTED_DIMENSIONS.get(format_name)
        if expected is not None and dimensions != expected:
            return [
                VisualReviewFinding(
                    "warn",
                    "image_dimensions",
                    f"Expected {expected[0]}x{expected[1]}, got {dimensions[0]}x{dimensions[1]}.",
                )
            ]
        return []

    def _prompt_contract(
        self,
        prompt: str,
        contract: ImagePromptContract,
    ) -> list[VisualReviewFinding]:
        missing = missing_required_terms(prompt, contract)
        if not missing:
            return []
        return [
            VisualReviewFinding(
                "fail",
                "prompt_contract",
                "Prompt is missing hard image contract values: " + ", ".join(missing),
            )
        ]

    def _references(self, references: list[ReferenceImage]) -> list[VisualReviewFinding]:
        if not references:
            return [
                VisualReviewFinding(
                    "fail",
                    "references",
                    "No selected references were attached to this visual run.",
                )
            ]
        categories = {reference.category for reference in references}
        required_groups = {
            "layout": "layouts/",
            "character": "character/",
            "orthosis": "orthosis/",
        }
        findings: list[VisualReviewFinding] = []
        for label, prefix in required_groups.items():
            if not any(category.startswith(prefix) for category in categories):
                findings.append(
                    VisualReviewFinding(
                        "warn",
                        "references",
                        f"No {label} reference selected.",
                    )
                )
        return findings

    def _carousel_sources(self, carousel_source_count: int) -> list[VisualReviewFinding]:
        if carousel_source_count >= 4:
            return []
        return [
            VisualReviewFinding(
                "fail",
                "carousel_sources",
                f"Carousel requires at least 4 distinct base images: 3 content slides plus image-backed CTA, got {carousel_source_count}.",
            )
        ]

    def _semantic_review(
        self,
        image_path: Path,
        references: list[ReferenceImage],
    ) -> list[VisualReviewFinding]:
        if not self.api_key:
            return [
                VisualReviewFinding(
                    "fail",
                    "vision_review",
                    "No API key available for semantic vision review. Image cannot be marked PASS.",
                )
            ]
        try:
            from openai import OpenAI
        except ImportError:
            return [
                VisualReviewFinding(
                    "fail",
                    "vision_review",
                    "OpenAI SDK is not installed. Image cannot be semantically reviewed.",
                )
            ]

        prompt = _semantic_review_prompt(references)
        try:
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": _image_data_url(image_path)},
                            },
                        ],
                    }
                ],
            )
            content = response.choices[0].message.content or "{}"
            payload = _extract_json(content)
        except Exception as exc:
            return [
                VisualReviewFinding(
                    "fail",
                    "vision_review",
                    f"Semantic vision review failed: {exc}",
                )
            ]

        findings: list[VisualReviewFinding] = []
        for issue in payload.get("issues", []):
            findings.append(
                VisualReviewFinding(
                    "fail",
                    "vision_review",
                    str(issue),
                )
            )
        for warning in payload.get("warnings", []):
            findings.append(
                VisualReviewFinding(
                    "warn",
                    "vision_review",
                    str(warning),
                )
            )
        if payload.get("pass") is not True and not findings:
            findings.append(
                VisualReviewFinding(
                    "fail",
                    "vision_review",
                    "Vision reviewer did not return pass=true.",
                )
            )
        return findings

    def _correction_prompt(self, findings: list[VisualReviewFinding]) -> str:
        if not findings:
            return (
                "No deterministic correction needed. Run human or vision-model review for semantic checks "
                "before marking the post final."
            )
        issues = "\n".join(f"- {finding.message}" for finding in findings)
        return f"""Revise the generated image while preserving the Perspective OS image contract.

Fix these issues:
{issues}

Keep: natural smartphone documentary style, person first, lifestyle first, visible aids only as everyday context, face not visible, left-leg orthosis consistency, safe 4:5 layout.
Avoid: pity, shock, fetish angle, fantasy orthosis, futuristic exoskeleton, studio look, overloaded infographic, 4-panel collage.
"""

    def _status(self, findings: list[VisualReviewFinding]) -> str:
        severities = {finding.severity for finding in findings}
        if "fail" in severities:
            return "fail"
        if "warn" in severities:
            return "warn"
        return "pass"


def _png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
    except OSError:
        return None
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", header[16:24])


def _image_data_url(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{encoded}"


def _extract_json(content: str) -> dict[str, object]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1:
        stripped = stripped[start : end + 1]
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return {
            "pass": False,
            "issues": [f"Vision reviewer returned non-JSON output: {content[:300]}"],
            "warnings": [],
        }


def _semantic_review_prompt(references: list[ReferenceImage]) -> str:
    reference_summary = "\n".join(
        f"- {reference.category}: {reference.description}"
        for reference in references
    )
    return f"""You are the Perspective OS visual gatekeeper. Review the generated image against this contract.

Hard FAIL if any of these are true:
- The face is visible or the image is a face-focused portrait.
- The orthosis is absent, not on the viewer/camera-left side of the image, fantasy-like, futuristic, missing side joints, missing broad straps, or not dark textile/medical-looking.
- The image copies visible text, labels, stickers, slogans, UI bars, or graphic layout elements from references.
- The image is an overloaded infographic, collage, 4-panel layout, or studio/glossy AI look.
- Body shape is far from the reference/contract: too model-like, too slim, exaggerated waist, wrong silhouette.
- Assistive devices dominate instead of everyday lifestyle context.
- The image sexualizes the orthosis, incontinence product, tights, body, or pose.

Warn if any of these are true:
- Hair is visible but does not resemble the reference: dark blond, smooth, high ponytail, everyday styling.
- Outfit drifts away from the reference family: black fitted top or polo, black shorts, black tights/leggings, white orthopedic shoes when visible.
- The generated person is not placed with enough negative space for deterministic overlay text.
- Orthosis proportions are plausible but too generic compared with the reference construction.

Reference intent:
{reference_summary}

Return ONLY JSON with this schema:
{{
  "pass": true or false,
  "issues": ["hard failure issue"],
  "warnings": ["non-blocking concern"],
  "observations": ["short factual observation"]
}}
"""
