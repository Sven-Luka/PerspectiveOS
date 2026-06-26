try:
    from ..brain.index import IndexedKnowledge
    from .context import CreativeContextBuilder, CreativeInputs
except ImportError:
    from brain.index import IndexedKnowledge
    from creative.context import CreativeContextBuilder, CreativeInputs


class CaptionEngine:
    """Generates short, medium, and long captions from Perspective OS knowledge."""

    def __init__(self, knowledge: IndexedKnowledge) -> None:
        """Create a caption engine bound to the current KnowledgeIndex."""
        self.knowledge = knowledge

    def generate(self, inputs: CreativeInputs) -> str:
        """Generate short, medium, and long caption variants."""
        context = CreativeContextBuilder(self.knowledge).build(inputs)
        short = (
            f"{context.location}, {context.outfit}, und ein kleiner Perspektivwechsel. "
            f"{context.perspective_sentence} {context.cta}"
        )
        medium = (
            f"Heute: {context.location}, {context.outfit}, {context.aid_visibility} sichtbar genug, "
            "um falsch verstanden zu werden, aber nicht wichtig genug, um den ganzen Menschen zu ersetzen.\n\n"
            f"Wie bei {context.metaphor}: {context.metaphor_line}\n\n"
            f"{context.perspective_sentence}\n\n{context.cta}"
        )
        long = (
            f"Es gibt Momente, da schaut jemand zuerst auf {context.aid_visibility}.\n\n"
            f"Eigentlich geht es aber um {context.location}, um {context.outfit}, um Alltag, Bewegung, Kaffee, "
            "Wege, kleine Entscheidungen und darum, sich nicht aus dem eigenen Leben herauszustylen.\n\n"
            f"Die bessere Metapher ist {context.metaphor}: {context.metaphor_line}\n\n"
            f"{context.perspective_sentence}\n\n"
            f"Ton: {context.tone}. Nicht: {context.avoid}.\n\n{context.cta}"
        )
        return f"""# Captions

## Short
{short}

## Medium
{medium}

## Long
{long}

## Hashtags
#PerspectiveOS #Sichtbarkeit #Alltag #Outfit #Perspektivwechsel
"""
