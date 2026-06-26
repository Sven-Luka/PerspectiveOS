"""Deterministic conversion of a creator-written carousel brief into production artifacts."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class StorySlide:
    """One submitted carousel slide with its preserved instructions."""

    number: int
    content: str


class FreeStoryBrief:
    """Keep a creator's wording intact while exposing slide-level direction."""

    _SLIDE = re.compile(
        r"^#\s*Perspective Carousel\s*(?:\u2013|\u2014|-|\?)\s*Slide\s*(\d+)\s*$",
        re.MULTILINE | re.IGNORECASE,
    )

    def __init__(self, source: str) -> None:
        self.source = source.strip()

    @property
    def is_present(self) -> bool:
        return bool(self.source)

    def slides(self) -> list[StorySlide]:
        matches = list(self._SLIDE.finditer(self.source))
        if not matches:
            return []
        slides: list[StorySlide] = []
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(self.source)
            slides.append(StorySlide(number=int(match.group(1)), content=self.source[match.end():end].strip()))
        return slides

    def carousel_markdown(self, format_name: str) -> str:
        slides = self.slides()
        if not slides:
            return ""
        sections = ["# Carousel", "", "## Format", format_name, "", "## Creator Story Contract"]
        sections.append("The following slide content was supplied by the creator and takes priority over generic carousel copy.")
        for slide in slides:
            sections.extend(("", f"## Slide {slide.number}", slide.content))
        return "\n".join(sections) + "\n"

    def prompt_addendum(self) -> str:
        slides = self.slides()
        if not slides:
            return ""
        sections = ["## Creator-Supplied Carousel Contract", "Use these slide directions verbatim as the production content. Keep the CI and hard character contract above."]
        for slide in slides:
            sections.extend(("", f"### Slide {slide.number}", slide.content))
        return "\n".join(sections) + "\n"
