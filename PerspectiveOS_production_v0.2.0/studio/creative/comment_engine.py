try:
    from ..brain.index import IndexedKnowledge
    from .context import CreativeContextBuilder, CreativeInputs
except ImportError:
    from brain.index import IndexedKnowledge
    from creative.context import CreativeContextBuilder, CreativeInputs


class CommentEngine:
    """Generates deterministic comment strategy and community responses."""

    def __init__(self, knowledge: IndexedKnowledge) -> None:
        """Create a comment engine bound to the current KnowledgeIndex."""
        self.knowledge = knowledge

    def generate(self, inputs: CreativeInputs) -> str:
        """Generate top comment, pinned comment, questions, and answer styles."""
        context = CreativeContextBuilder(self.knowledge).build(inputs)
        questions = [
            "Ist das nicht unangenehm, wenn man es sieht?",
            "Warum versteckst du das nicht einfach?",
            "Ist die Orthese immer am gleichen Bein?",
            "Wie findest du Outfits, die dazu passen?",
            "Darf man dazu respektvoll Fragen stellen?",
        ]
        answers = [
            "Sichtbar heisst nicht automatisch Mittelpunkt. Es gehoert einfach zum Alltag.",
            f"Weil Kleidung Ausdruck ist. {context.outfit} ist kein Versteck.",
            "Ja, Konsistenz ist wichtig: Hilfsmittel muessen glaubwuerdig und respektvoll dargestellt werden.",
            "Ich starte mit Alltag und Bewegung, nicht mit Tarnung.",
            "Ja. Respekt reicht als Einstieg meistens voellig.",
        ]
        lines = [
            "# Comments",
            "",
            "## Top Comment",
            f"{context.perspective_sentence}",
            "",
            "## Pinned Comment",
            f"{context.cta}",
            "",
            "## Likely Community Questions",
        ]
        for index, question in enumerate(questions, start=1):
            lines.extend([f"{index}. {question}", f"   Suggested answer: {answers[index - 1]}"])
        lines.extend(
            [
                "",
                "## Humorous Answer",
                f"Ich wollte eigentlich nur {context.location}. Die Perspektive hat sich selbst eingeladen.",
                "",
                "## Respectful Answer",
                "Nicht alles, was sichtbar ist, ist eine Einladung zur Bewertung. Dieser Account zeigt Alltag.",
            ]
        )
        return "\n".join(lines) + "\n"
