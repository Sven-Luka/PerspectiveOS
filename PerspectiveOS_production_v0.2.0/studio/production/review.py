import json
from dataclasses import dataclass
from datetime import datetime

try:
    from ..brain.index import IndexedKnowledge
    from ..core.knowledge import bullets
    from ..image.prompt_contract import ImagePromptContractBuilder, missing_required_terms
except ImportError:
    from brain.index import IndexedKnowledge
    from core.knowledge import bullets
    from image.prompt_contract import ImagePromptContractBuilder, missing_required_terms


REQUIRED_FILES = (
    "brief.md",
    "hooks.md",
    "caption.md",
    "carousel.md",
    "image_contract.md",
    "reference_manifest.md",
    "reference_manifest.json",
    "image_prompt.md",
    "video_prompt.md",
    "comments.md",
    "story.md",
    "checklist.md",
    "metadata.json",
)

REQUIRED_METADATA_FIELDS = (
    "version",
    "created_at",
    "topic",
    "target_emotion",
    "image_type",
    "location",
    "outfit",
    "aid_visibility",
    "metaphor",
    "format",
)

BIBLE_GATES = (
    ("Lifestyle leads", ("Lifestyle", "Alltag")),
    ("Human-first framing", ("person", "Menschen", "Character", "Figur")),
    ("Warm humor", ("warm", "Humor", "freundlich")),
    ("Perspective shift", ("Perspektive", "perspective")),
    ("No pity/shock/fetish framing", ("No pity", "no shock", "no fetish")),
)


@dataclass(frozen=True)
class ReviewFinding:
    """One automated review finding for a generated production folder."""

    severity: str
    check: str
    message: str


@dataclass(frozen=True)
class ProductionReview:
    """Machine-readable automated review result."""

    status: str
    generated_at: str
    findings: list[ReviewFinding]

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "generated_at": self.generated_at,
            "findings": [
                {
                    "severity": finding.severity,
                    "check": finding.check,
                    "message": finding.message,
                }
                for finding in self.findings
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def to_markdown(self) -> str:
        lines = [
            "# Automation Review",
            "",
            f"Status: {self.status.upper()}",
            f"Generated at: {self.generated_at}",
            "",
            "## Findings",
        ]
        if not self.findings:
            lines.append("- No automated findings.")
        else:
            for finding in self.findings:
                lines.append(f"- [{finding.severity.upper()}] {finding.check}: {finding.message}")
        lines.extend(
            [
                "",
                "## Review Meaning",
                "PASS means the generated folder satisfies the automated production gates.",
                "WARN means a human review should resolve the listed issues before visual production.",
                "FAIL means required files or machine-readable metadata are missing or invalid.",
            ]
        )
        return "\n".join(lines) + "\n"


class ProductionReviewer:
    """Checks generated production folders against the Perspective OS production bible."""

    def __init__(self, knowledge: IndexedKnowledge) -> None:
        self.knowledge = knowledge

    def review(self, files: dict[str, str]) -> ProductionReview:
        findings: list[ReviewFinding] = []
        findings.extend(self._required_files(files))
        findings.extend(self._metadata(files.get("metadata.json", "")))
        findings.extend(self._bible_gates(files))
        findings.extend(self._image_prompt_contract(files.get("image_prompt.md", "")))
        findings.extend(self._banned_language(files))
        status = self._status(findings)
        return ProductionReview(
            status=status,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            findings=findings,
        )

    def _required_files(self, files: dict[str, str]) -> list[ReviewFinding]:
        findings: list[ReviewFinding] = []
        for file_name in REQUIRED_FILES:
            content = files.get(file_name, "")
            if file_name not in files:
                findings.append(
                    ReviewFinding("fail", "required_files", f"Missing required file: {file_name}")
                )
            elif not content.strip():
                findings.append(
                    ReviewFinding("fail", "required_files", f"Required file is empty: {file_name}")
                )
        return findings

    def _metadata(self, content: str) -> list[ReviewFinding]:
        if not content.strip():
            return [ReviewFinding("fail", "metadata", "metadata.json is empty or missing.")]
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            return [ReviewFinding("fail", "metadata", f"metadata.json is not valid JSON: {exc}")]

        findings: list[ReviewFinding] = []
        for field in REQUIRED_METADATA_FIELDS:
            if not str(payload.get(field, "")).strip():
                findings.append(
                    ReviewFinding("fail", "metadata", f"Missing metadata field: {field}")
                )
        if payload.get("knowledge_missing"):
            findings.append(
                ReviewFinding(
                    "warn",
                    "metadata",
                    "Repository knowledge has missing source documents listed in metadata.",
                )
            )
        return findings

    def _bible_gates(self, files: dict[str, str]) -> list[ReviewFinding]:
        corpus = "\n".join(files.values()).lower()
        findings: list[ReviewFinding] = []
        for check, terms in BIBLE_GATES:
            if not any(term.lower() in corpus for term in terms):
                findings.append(
                    ReviewFinding(
                        "warn",
                        "bible_gate",
                        f"Could not confirm gate from generated copy: {check}",
                    )
                )
        return findings

    def _image_prompt_contract(self, prompt: str) -> list[ReviewFinding]:
        if not prompt.strip():
            return [ReviewFinding("fail", "image_prompt_contract", "image_prompt.md is empty.")]
        contract = ImagePromptContractBuilder(self.knowledge).build()
        missing = missing_required_terms(prompt, contract)
        if not missing:
            return []
        return [
            ReviewFinding(
                "fail",
                "image_prompt_contract",
                "Image prompt is missing hard contract values: " + ", ".join(missing),
            )
        ]

    def _banned_language(self, files: dict[str, str]) -> list[ReviewFinding]:
        banned_terms = bullets(self.knowledge.document("creative/LanguageBible.md"), "Wörter vermeiden")
        if not banned_terms:
            banned_terms = bullets(self.knowledge.document("creative/LanguageBible.md"), "Woerter vermeiden")

        searchable = {
            name: self._copy_for_language_scan(content).lower()
            for name, content in files.items()
            if name not in {"automation_review.md", "automation_review.json"}
        }
        findings: list[ReviewFinding] = []
        for term in banned_terms:
            needle = term.strip().lower()
            if not needle:
                continue
            for file_name, content in searchable.items():
                if needle in content:
                    findings.append(
                        ReviewFinding(
                            "warn",
                            "language_bible",
                            f"Potentially avoided wording appears in {file_name}: {term}",
                        )
                    )
        return findings

    def _copy_for_language_scan(self, content: str) -> str:
        lines: list[str] = []
        for line in content.splitlines():
            normalized = line.strip().lower()
            if " and avoid " in normalized:
                continue
            if normalized.startswith("ton:") and " nicht:" in normalized:
                continue
            if normalized.startswith("avoid:") or normalized.startswith("nicht:"):
                continue
            lines.append(line)
        return "\n".join(lines)

    def _status(self, findings: list[ReviewFinding]) -> str:
        severities = {finding.severity for finding in findings}
        if "fail" in severities:
            return "fail"
        if "warn" in severities:
            return "warn"
        return "pass"
