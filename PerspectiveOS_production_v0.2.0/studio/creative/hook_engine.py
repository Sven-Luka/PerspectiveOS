try:
    from ..brain.index import IndexedKnowledge
    from .context import CreativeContextBuilder, CreativeInputs
except ImportError:
    from brain.index import IndexedKnowledge
    from creative.context import CreativeContextBuilder, CreativeInputs


class HookEngine:
    """Generates deterministic hook variants from repository knowledge."""

    def __init__(self, knowledge: IndexedKnowledge) -> None:
        """Create a hook engine bound to the current KnowledgeIndex."""
        self.knowledge = knowledge

    def generate(self, inputs: CreativeInputs) -> str:
        """Generate five categorized hook variants."""
        context = CreativeContextBuilder(self.knowledge).build(inputs)
        variants = {
            "Curiosity": f"Was verandert sich, wenn du zuerst {context.outfit} siehst?",
            "Humor": f"Ich wollte nur {context.location}. {context.metaphor} hatte andere Plaene.",
            "Perspective Shift": context.hook,
            "Unexpected": f"Man sieht {context.aid_visibility}. Und trotzdem beginnt die Geschichte woanders.",
            "Conversation Starter": f"Welche Perspektive fehlt, wenn man nur auf {context.aid_visibility} schaut?",
        }
        lines = ["# Hooks", ""]
        for category, hook in variants.items():
            lines.extend([f"## {category}", hook, ""])
        return "\n".join(lines).strip() + "\n"
