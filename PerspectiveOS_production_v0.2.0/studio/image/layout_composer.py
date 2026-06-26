from dataclasses import dataclass
from pathlib import Path
import textwrap

try:
    from ..core.settings import ProjectSettings
except ImportError:
    from core.settings import ProjectSettings


class LayoutCompositionError(RuntimeError):
    """Raised when deterministic layout composition cannot run."""


@dataclass(frozen=True)
class ComposedLayout:
    """A composed Perspective OS layout preview."""

    path: Path
    relative_path: str
    file_name: str
    image_bytes: bytes


@dataclass(frozen=True)
class LayoutContent:
    """Text and icon content for a single Perspective layout slide."""

    series_label: str
    headline: str
    highlight: str
    icon_labels: tuple[str, ...]
    body_text: str = ""
    slide_number: int = 1
    slide_count: int = 3
    slide_kind: str = "hook"


class LayoutComposer:
    """Composes deterministic Perspective OS overlay layouts on generated photos."""

    CANVAS = (1080, 1350)
    PURPLE = "#6C3CF0"
    NEON = "#BFFF00"
    WHITE = "#FFFFFF"
    BLACK = "#111111"
    TEAL = "#21B8C7"

    def __init__(self, settings: ProjectSettings | None = None) -> None:
        self.settings = settings or ProjectSettings()

    def compose_feed_slide(
        self,
        *,
        source_image: Path,
        folder_path: Path,
        content: LayoutContent,
        file_name: str = "layout_preview.png",
        repository_root: Path | None = None,
    ) -> ComposedLayout:
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError as exc:  # pragma: no cover - dependency hint
            raise LayoutCompositionError(
                "The 'Pillow' package is not installed. Run: pip install -r requirements.txt"
            ) from exc

        if not source_image.exists():
            raise LayoutCompositionError(f"Missing source image: {source_image}")

        canvas = Image.open(source_image).convert("RGB")
        canvas = _cover_resize(canvas, self.CANVAS, anchor="right")
        overlay = ImageDraw.Draw(canvas, "RGBA")
        fonts = _fonts(ImageFont)

        self._text_shadow_panel(overlay, content.slide_kind)
        if content.slide_kind == "cta":
            self._cta_layout(canvas, overlay, content, fonts)
        elif content.slide_number == 1:
            self._hook_layout(canvas, overlay, content, fonts)
        else:
            self._detail_layout(canvas, overlay, content, fonts)
        self._slide_counter(
            overlay,
            content.slide_number,
            content.slide_count,
            fonts["small_bold"],
            on_light=content.slide_kind == "cta",
        )
        self._signature(canvas, overlay, fonts["script"], fonts["small_bold"], on_light=content.slide_kind == "cta")

        folder_path.mkdir(parents=True, exist_ok=True)
        output = folder_path / file_name
        canvas.save(output, format="PNG")
        image_bytes = output.read_bytes()
        return ComposedLayout(
            path=output,
            relative_path=self._display_path(output, repository_root),
            file_name=file_name,
            image_bytes=image_bytes,
        )

    def compose_carousel(
        self,
        *,
        source_images: list[Path],
        folder_path: Path,
        contents: list[LayoutContent],
        repository_root: Path | None = None,
    ) -> list[ComposedLayout]:
        if len(contents) < 3:
            raise LayoutCompositionError("Carousel requires at least 3 content slides.")
        if not source_images:
            raise LayoutCompositionError("Carousel requires at least one source image.")
        layouts: list[ComposedLayout] = []
        for index, content in enumerate(contents):
            source = source_images[min(index, len(source_images) - 1)]
            layouts.append(
                self.compose_feed_slide(
                    source_image=source,
                    folder_path=folder_path,
                    content=content,
                    file_name=f"carousel_slide_{index + 1:02d}.png",
                    repository_root=repository_root,
                )
            )
        return layouts

    def _text_shadow_panel(self, draw, slide_kind: str) -> None:
        return

    def _badge(self, draw, xy: tuple[int, int], text: str, font) -> None:
        x, y = xy
        width = 330 if text == "ANDERS GEDACHT" else max(260, min(430, _text_width(draw, text, font) + 38))
        draw.rounded_rectangle((x, y, x + width, y + 56), radius=2, fill=self.PURPLE)
        draw.text((x + 18, y + 14), text, fill=self.WHITE, font=font)
        draw.line((x, y + 70, x + width - 10, y + 60), fill=self.NEON, width=5)

    def _headline(self, draw, xy: tuple[int, int], text: str, font) -> None:
        x, y = xy
        line_height = _line_height(font, fallback=76)
        for index, line in enumerate(_wrap(text, width=13, max_lines=4)):
            draw.text((x, y + index * line_height), line, fill=self.WHITE, font=font)

    def _body_text(self, draw, xy: tuple[int, int], text: str, font) -> None:
        x, y = xy
        for index, line in enumerate(_wrap(text, width=24, max_lines=5)):
            draw.text((x, y + index * 42), line, fill=self.WHITE, font=font)

    def _highlight(self, draw, xy: tuple[int, int], text: str, font) -> None:
        x, y = xy
        lines = _wrap(text, width=18, max_lines=2)
        line_height = 62
        width = min(545, max(360, max(_text_width(draw, line, font) for line in lines) + 42))
        draw.rounded_rectangle(
            (x, y, x + width, y + len(lines) * line_height + 20),
            radius=8,
            fill=self.NEON,
        )
        for index, line in enumerate(lines):
            draw.text((x + 18, y + 12 + index * line_height), line, fill=self.BLACK, font=font)

    def _smile(self, draw, center: tuple[int, int]) -> None:
        x, y = center
        draw.arc((x - 42, y - 35, x + 42, y + 45), 25, 155, fill=self.PURPLE, width=7)
        draw.ellipse((x - 22, y - 20, x - 14, y - 12), fill=self.PURPLE)
        draw.ellipse((x + 15, y - 22, x + 23, y - 14), fill=self.PURPLE)

    def _bottom_icons(self, canvas, draw, labels: tuple[str, ...], font, label_font) -> None:
        y = 1095
        centers = [(105, y), (285, y), (465, y)]
        colors = [self.PURPLE, self.NEON, self.TEAL]
        for index, label in enumerate(labels[:3]):
            x, cy = centers[index]
            draw.ellipse((x - 51, cy - 51, x + 51, cy + 51), fill=colors[index])
            icon_fill = self.WHITE if index != 1 else self.BLACK
            icon_key = _icon_key(label, index)
            if not self._paste_icon_asset(canvas, icon_key, (x, cy), icon_fill, size=62):
                self._draw_ui_kit_icon(draw, icon_key, (x, cy), icon_fill, size=62)
            for line_index, line in enumerate(_wrap(label.upper(), width=13, max_lines=2)):
                _draw_centered_text(
                    draw,
                    (x - 86, cy + 62 + line_index * 27, x + 86, cy + 88 + line_index * 27),
                    line,
                    fill=self.WHITE,
                    font=label_font,
                )

    def _draw_ui_kit_icon(self, draw, icon_key: str, center: tuple[int, int], fill: str, size: int = 64) -> None:
        if icon_key == "diaper":
            self._draw_diaper(draw, center, fill, size)
        elif icon_key == "orthosis":
            self._draw_orthosis(draw, center, fill, size)
        elif icon_key == "outfit":
            self._draw_shirt(draw, center, fill, size)
        elif icon_key == "follow":
            self._draw_chat(draw, center, fill, size)
        elif icon_key == "camera":
            self._draw_camera(draw, center, fill, size)
        elif icon_key == "heart":
            self._draw_heart(draw, center, fill, size)
        elif icon_key == "smile":
            self._draw_smile_icon(draw, center, fill, size)
        else:
            self._draw_drop(draw, center, fill, size)

    def _draw_drop(self, draw, center: tuple[int, int], fill: str, size: int = 64) -> None:
        x, y = center
        scale = size / 64
        stroke = max(3, round(5 * scale))
        draw.polygon(
            [
                (x, y - round(28 * scale)),
                (x - round(20 * scale), y + round(5 * scale)),
                (x, y + round(29 * scale)),
                (x + round(20 * scale), y + round(5 * scale)),
            ],
            outline=fill,
            width=stroke,
        )
        draw.arc(
            (
                x - round(20 * scale),
                y - round(4 * scale),
                x + round(20 * scale),
                y + round(35 * scale),
            ),
            20,
            160,
            fill=fill,
            width=stroke,
        )

    def _draw_diaper(self, draw, center: tuple[int, int], fill: str, size: int = 64) -> None:
        x, y = center
        scale = size / 64
        stroke = max(3, round(4 * scale))
        draw.rounded_rectangle(
            (
                x - round(26 * scale),
                y - round(18 * scale),
                x + round(26 * scale),
                y + round(24 * scale),
            ),
            radius=round(8 * scale),
            outline=fill,
            width=stroke,
        )
        draw.line((x - round(17 * scale), y - round(2 * scale), x - round(4 * scale), y + round(17 * scale)), fill=fill, width=stroke)
        draw.line((x + round(17 * scale), y - round(2 * scale), x + round(4 * scale), y + round(17 * scale)), fill=fill, width=stroke)

    def _draw_shirt(self, draw, center: tuple[int, int], fill: str, size: int = 64) -> None:
        x, y = center
        scale = size / 64
        stroke = max(3, round(4 * scale))
        draw.line((x - round(27 * scale), y - round(18 * scale), x - round(10 * scale), y - round(28 * scale), x, y - round(14 * scale), x + round(10 * scale), y - round(28 * scale), x + round(27 * scale), y - round(18 * scale)), fill=fill, width=stroke)
        draw.line((x - round(20 * scale), y - round(14 * scale), x - round(17 * scale), y + round(28 * scale), x + round(17 * scale), y + round(28 * scale), x + round(20 * scale), y - round(14 * scale)), fill=fill, width=stroke)

    def _draw_orthosis(self, draw, center: tuple[int, int], fill: str, size: int = 64) -> None:
        x, y = center
        scale = size / 64
        draw.rounded_rectangle(
            (x - round(8 * scale), y - round(28 * scale), x + round(8 * scale), y + round(28 * scale)),
            radius=round(6 * scale),
            fill=fill,
        )
        for offset in (-16, 0, 16):
            draw.rounded_rectangle(
                (
                    x - round(25 * scale),
                    y + round(offset * scale) - round(4 * scale),
                    x + round(25 * scale),
                    y + round(offset * scale) + round(4 * scale),
                ),
                radius=round(4 * scale),
                fill=fill,
            )

    def _draw_camera(self, draw, center: tuple[int, int], fill: str, size: int = 64) -> None:
        x, y = center
        scale = size / 64
        stroke = max(3, round(4 * scale))
        draw.rounded_rectangle(
            (x - round(25 * scale), y - round(16 * scale), x + round(25 * scale), y + round(18 * scale)),
            radius=round(6 * scale),
            outline=fill,
            width=stroke,
        )
        draw.ellipse(
            (x - round(9 * scale), y - round(8 * scale), x + round(9 * scale), y + round(10 * scale)),
            outline=fill,
            width=stroke,
        )

    def _draw_chat(self, draw, center: tuple[int, int], fill: str, size: int = 64) -> None:
        x, y = center
        scale = size / 64
        stroke = max(3, round(4 * scale))
        draw.rounded_rectangle(
            (x - round(25 * scale), y - round(18 * scale), x + round(25 * scale), y + round(16 * scale)),
            radius=round(8 * scale),
            outline=fill,
            width=stroke,
        )
        draw.polygon(
            [
                (x - round(8 * scale), y + round(16 * scale)),
                (x - round(18 * scale), y + round(25 * scale)),
                (x - round(3 * scale), y + round(18 * scale)),
            ],
            fill=fill,
        )

    def _draw_heart(self, draw, center: tuple[int, int], fill: str, size: int = 64) -> None:
        x, y = center
        scale = size / 64
        stroke = max(3, round(5 * scale))
        draw.arc((x - round(30 * scale), y - round(28 * scale), x + round(4 * scale), y + round(22 * scale)), 120, 330, fill=fill, width=stroke)
        draw.arc((x - round(4 * scale), y - round(28 * scale), x + round(30 * scale), y + round(22 * scale)), 210, 60, fill=fill, width=stroke)
        draw.line((x - round(22 * scale), y + round(8 * scale), x, y + round(30 * scale), x + round(22 * scale), y + round(8 * scale)), fill=fill, width=stroke)

    def _draw_smile_icon(self, draw, center: tuple[int, int], fill: str, size: int = 64) -> None:
        x, y = center
        scale = size / 64
        stroke = max(3, round(5 * scale))
        draw.arc(
            (x - round(28 * scale), y - round(22 * scale), x + round(28 * scale), y + round(34 * scale)),
            20,
            160,
            fill=fill,
            width=stroke,
        )
        dot = max(4, round(5 * scale))
        draw.ellipse((x - round(18 * scale), y - round(10 * scale), x - round(18 * scale) + dot, y - round(10 * scale) + dot), fill=fill)
        draw.ellipse((x + round(12 * scale), y - round(10 * scale), x + round(12 * scale) + dot, y - round(10 * scale) + dot), fill=fill)

    def _slide_counter(self, draw, slide_number: int, slide_count: int, font, on_light: bool = False) -> None:
        draw.ellipse((45, 1260, 95, 1310), fill=self.PURPLE)
        draw.text((63, 1270), str(slide_number), fill=self.WHITE, font=font)
        draw.text((112, 1270), f"/ {slide_count}", fill=self.BLACK if on_light else self.WHITE, font=font)
        draw.line((48, 1324, 160, 1314), fill=self.NEON, width=4)

    def _signature(self, canvas, draw, script_font, small_font, on_light: bool = False) -> None:
        asset_name = "signature_made_by_jona_v2.png"
        if self._paste_brand_asset(canvas, asset_name, (735, 1040), width=290):
            return
        made_by_fill = self.PURPLE if on_light else self.WHITE
        draw.text((735, 1226), "made by", fill=made_by_fill, font=script_font)
        draw.text((842, 1252), "Jona", fill=self.NEON, font=script_font)
        self._signature_heart(draw, (1028, 1242), self.PURPLE)
        draw.line((810, 1330, 1032, 1308), fill=self.PURPLE, width=4)
        draw.line((842, 1340, 1050, 1326), fill=self.NEON, width=4)

    def _signature_heart(self, draw, center: tuple[int, int], fill: str) -> None:
        x, y = center
        draw.arc((x - 58, y - 35, x - 10, y + 30), 125, 330, fill=fill, width=6)
        draw.arc((x - 16, y - 35, x + 44, y + 30), 210, 58, fill=fill, width=6)
        draw.line((x - 44, y + 5, x - 3, y + 54), fill=fill, width=6)
        draw.line((x + 29, y + 4, x - 3, y + 54), fill=fill, width=6)

    def _paste_brand_asset(self, canvas, asset_name: str, xy: tuple[int, int], width: int) -> bool:
        asset = self._load_asset("brand", asset_name)
        if asset is None:
            return False
        resized = _resize_by_width(asset, width)
        canvas.paste(resized, xy, resized)
        return True

    def _paste_icon_asset(self, canvas, icon_key: str, center: tuple[int, int], fill: str, size: int) -> bool:
        asset = self._load_asset("icons_png", f"{icon_key}.png")
        if asset is None:
            return False
        resized = asset.resize((size, size))
        tinted = _tint_alpha_image(resized, fill)
        x, y = center
        canvas.paste(tinted, (x - size // 2, y - size // 2), tinted)
        return True

    def _load_asset(self, *parts: str):
        try:
            from PIL import Image
        except ImportError:
            return None
        path = self.settings.assets_dir / "references" / "layouts" / "ui_kit" / Path(*parts)
        if not path.exists():
            return None
        try:
            return Image.open(path).convert("RGBA")
        except OSError:
            return None

    def _hook_layout(self, canvas, draw, content: LayoutContent, fonts: dict[str, object]) -> None:
        self._paper_strip(canvas, "ANDERS GEDACHT", (52, 58), fonts["badge"], self.PURPLE, self.WHITE, angle=-2)
        draw.line((64, 142, 332, 130), fill=self.NEON, width=5)

        lines = _wrap(content.headline, width=14, max_lines=3)
        for index, line in enumerate(lines):
            fill = self.NEON if index == len(lines) - 1 else "#B168F4"
            self._paper_strip(
                canvas,
                line,
                (48 + index * 10, 220 + index * 98),
                fonts["headline"],
                fill,
                self.BLACK,
                angle=(-2 if index % 2 == 0 else 1),
            )
        self._paper_strip(
            canvas,
            content.highlight,
            (62, 545),
            fonts["highlight"],
            self.NEON,
            self.BLACK,
            angle=1,
        )
        self._draw_plus(draw, (620, 120), self.TEAL)
        self._draw_heart(draw, (622, 235), self.PURPLE, size=74)
        self._doodle_arrow(draw, (72, 750), self.PURPLE)
        self._bottom_action_band(canvas, draw, ("Folgen", "Echt", "Mit Humor"), fonts)

    def _detail_layout(self, canvas, draw, content: LayoutContent, fonts: dict[str, object]) -> None:
        self._paper_strip(canvas, content.series_label.upper(), (54, 62), fonts["badge"], self.PURPLE, self.WHITE, angle=-2)
        draw.line((64, 142, 330, 130), fill=self.NEON, width=5)
        self._paper_strip(canvas, content.headline, (54, 214), fonts["medium_headline"], "#B168F4", self.BLACK, angle=-1)
        if content.highlight:
            self._paper_strip(canvas, content.highlight, (66, 350), fonts["highlight"], self.NEON, self.BLACK, angle=1)
        if content.body_text:
            for index, line in enumerate(_wrap(content.body_text, width=28, max_lines=3)):
                _shadowed_text(draw, (70, 500 + index * 42), line, self.WHITE, self.PURPLE, fonts["body"])
        self._draw_plus(draw, (622, 130), self.TEAL)
        self._draw_heart(draw, (640, 242), self.PURPLE, size=68)
        self._bottom_action_band(canvas, draw, ("Folgen", "Echt", "Mit Humor"), fonts)

    def _cta_layout(self, canvas, draw, content: LayoutContent, fonts: dict[str, object]) -> None:
        self._paper_strip(canvas, "ANDERS GEDACHT", (52, 58), fonts["badge"], self.PURPLE, self.WHITE, angle=-2)
        draw.line((64, 142, 332, 130), fill=self.NEON, width=5)
        self._paper_strip(canvas, "Du bist nicht", (54, 215), fonts["headline"], "#B168F4", self.BLACK, angle=-2)
        self._paper_strip(canvas, "allein damit.", (72, 312), fonts["headline"], "#B168F4", self.BLACK, angle=1)
        self._paper_strip(canvas, "Bleib bei mir.", (52, 430), fonts["headline"], self.NEON, self.BLACK, angle=-1)
        self._paper_strip(canvas, "echt. unzensiert. mit Humor.", (78, 565), fonts["small_bold"], self.PURPLE, self.WHITE, angle=1)

        self._draw_plus(draw, (620, 116), self.TEAL)
        self._draw_heart(draw, (616, 235), self.PURPLE, size=74)
        self._doodle_arrow(draw, (68, 720), self.PURPLE)
        self._paper_strip(canvas, "Folge für ehrliche Einblicke.", (66, 748), fonts["small_bold"], self.NEON, self.BLACK, angle=-1)
        self._bottom_action_band(canvas, draw, ("Folgen", "Echt", "Mit Humor"), fonts)

    def _bottom_action_band(self, canvas, draw, labels: tuple[str, ...], fonts: dict[str, object]) -> None:
        top = 1170
        draw.rectangle((0, top, 1080, 1350), fill=self.TEAL)
        self._paper_strip(canvas, labels[0] if labels else "Folgen", (62, 1204), fonts["medium_headline"], self.PURPLE, self.WHITE, angle=-2)
        items = labels[1:3] if len(labels) >= 3 else ("Echt", "Mit Humor")
        centers = [(520, 1234), (756, 1234)]
        icon_keys = ("heart", "smile")
        for index, (center, label) in enumerate(zip(centers, items)):
            x, _ = center
            if index:
                draw.line((x - 118, 1200, x - 118, 1325), fill=(255, 255, 255, 120), width=2)
            self._draw_ui_kit_icon(draw, icon_keys[index], (x, 1218), self.BLACK, size=46)
            _draw_centered_text(draw, (x - 95, 1260, x + 95, 1302), label, fill=self.BLACK, font=fonts["small"])

    def _paper_strip(self, canvas, text: str, xy: tuple[int, int], font, fill: str, text_fill: str, angle: int = 0) -> None:
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            return
        measure = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        bbox = measure.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        width = text_width + 42
        height = text_height + 34
        strip = Image.new("RGBA", (width + 12, height + 12), (0, 0, 0, 0))
        strip_draw = ImageDraw.Draw(strip)
        strip_draw.polygon(
            [(7, 6), (width + 4, 2), (width + 9, height + 4), (3, height + 9)],
            fill=fill,
        )
        strip_draw.text((24, 15), text, fill=text_fill, font=font)
        rotated = strip.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
        canvas.paste(rotated, xy, rotated)

    def _draw_plus(self, draw, center: tuple[int, int], fill: str) -> None:
        x, y = center
        draw.ellipse((x - 54, y - 54, x + 54, y + 54), fill=fill)
        draw.rectangle((x - 10, y - 32, x + 10, y + 32), fill=self.WHITE)
        draw.rectangle((x - 32, y - 10, x + 32, y + 10), fill=self.WHITE)

    def _doodle_arrow(self, draw, start: tuple[int, int], fill: str) -> None:
        x, y = start
        draw.arc((x, y, x + 135, y + 120), 110, 260, fill=fill, width=6)
        draw.line((x + 106, y + 100, x + 129, y + 120), fill=fill, width=6)
        draw.line((x + 129, y + 120, x + 97, y + 124), fill=fill, width=6)

    def _display_path(self, path: Path, repository_root: Path | None) -> str:
        if repository_root is not None:
            try:
                return path.relative_to(repository_root).as_posix()
            except ValueError:
                pass
        return path.as_posix()


def _fonts(image_font) -> dict[str, object]:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]

    def load(size: int, bold: bool = False):
        path = candidates[0 if bold else 1]
        try:
            return image_font.truetype(path, size=size)
        except OSError:
            return image_font.load_default()

    return {
        "badge": load(26, True),
        "headline": load(62, True),
        "hero": load(84, True),
        "medium_headline": load(46, True),
        "highlight": load(42, True),
        "body": load(32, False),
        "small": load(25, True),
        "small_bold": load(28, True),
        "tiny_bold": load(22, True),
        "script": _load_script(image_font, 45),
    }


def _load_script(image_font, size: int):
    for path in ("C:/Windows/Fonts/segoesc.ttf", "C:/Windows/Fonts/ariali.ttf", "C:/Windows/Fonts/arial.ttf"):
        try:
            return image_font.truetype(path, size=size)
        except OSError:
            continue
    return image_font.load_default()


def _cover_resize(image, size: tuple[int, int], anchor: str = "center"):
    source_ratio = image.width / image.height
    target_ratio = size[0] / size[1]
    if source_ratio > target_ratio:
        new_height = size[1]
        new_width = round(new_height * source_ratio)
    else:
        new_width = size[0]
        new_height = round(new_width / source_ratio)
    resized = image.resize((new_width, new_height))
    if anchor == "right":
        left = max(0, new_width - size[0])
    elif anchor == "left":
        left = 0
    else:
        left = (new_width - size[0]) // 2
    top = (new_height - size[1]) // 2
    return resized.crop((left, top, left + size[0], top + size[1]))


def _wrap(text: str, width: int, max_lines: int) -> list[str]:
    lines = textwrap.wrap(text.strip(), width=width) or [text.strip()]
    return lines[:max_lines]


def _text_width(draw, text: str, font) -> int:
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]
    except AttributeError:
        return len(text) * 12


def _resize_by_width(image, width: int):
    height = max(1, round(image.height * (width / image.width)))
    return image.resize((width, height))


def _tint_alpha_image(image, fill: str):
    try:
        from PIL import Image, ImageColor
    except ImportError:
        return image
    color = ImageColor.getrgb(fill)
    alpha = image.getchannel("A")
    tinted = Image.new("RGBA", image.size, color + (0,))
    tinted.putalpha(alpha)
    return tinted


def _icon_key(label: str, fallback_index: int) -> str:
    normalized = label.lower()
    if any(term in normalized for term in ("drang", "aufhalten")):
        return "drop"
    if any(term in normalized for term in ("windel", "sitz", "größe", "groesse", "auslauf")):
        return "diaper"
    if any(term in normalized for term in ("body", "slip", "outfit", "kleid", "shirt")):
        return "outfit"
    if any(term in normalized for term in ("orth", "schiene", "hilfe")):
        return "orthosis"
    if any(term in normalized for term in ("mutmach", "herz")):
        return "heart"
    if any(term in normalized for term in ("anders", "smile", "lächel", "laechel")):
        return "smile"
    if any(term in normalized for term in ("ehrlich", "follow", "folge", "kommentar")):
        return "follow"
    if any(term in normalized for term in ("blick", "kamera", "foto")):
        return "camera"
    return ("drop", "diaper", "outfit")[min(fallback_index, 2)]


def _line_height(font, fallback: int) -> int:
    try:
        bbox = font.getbbox("Ag")
        return bbox[3] - bbox[1] + 16
    except AttributeError:
        return fallback


def _draw_centered_text(draw, box: tuple[int, int, int, int], text: str, fill: str, font) -> None:
    left, top, right, bottom = box
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
    except AttributeError:
        width = len(text) * 10
        height = 20
    x = left + max(0, (right - left - width) // 2)
    y = top + max(0, (bottom - top - height) // 2)
    draw.text((x, y), text, fill=fill, font=font)


def _shadowed_text(draw, xy: tuple[int, int], text: str, fill: str, shadow_fill: str, font) -> None:
    x, y = xy
    draw.text((x + 3, y + 3), text, fill=shadow_fill, font=font)
    draw.text((x, y), text, fill=fill, font=font)
