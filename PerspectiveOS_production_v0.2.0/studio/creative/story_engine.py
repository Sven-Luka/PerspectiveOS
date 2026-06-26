try:
    from ..brain.index import IndexedKnowledge
    from .context import CreativeContextBuilder, CreativeInputs
except ImportError:
    from brain.index import IndexedKnowledge
    from creative.context import CreativeContextBuilder, CreativeInputs


class StoryEngine:
    """Generates deterministic Instagram Story sequences."""

    def __init__(self, knowledge: IndexedKnowledge) -> None:
        """Create a story engine bound to the current KnowledgeIndex."""
        self.knowledge = knowledge

    def generate(self, inputs: CreativeInputs) -> str:
        """Generate a four-frame Instagram Story sequence."""
        context = CreativeContextBuilder(self.knowledge).build(inputs)
        return f"""# Instagram Story

## Frame 1 - Question
Text: Was siehst du zuerst: {context.outfit}, {context.aid_visibility}, oder die Situation?
Visual: {context.location}, natural smartphone framing.

## Frame 2 - Behind the Scenes
Text: Outfit zuerst. Hilfsmittel begleiten.
Visual: Small preparation moment, {context.photo_perspectives}.

## Frame 3 - Result
Text: {context.perspective_sentence}
Visual: Finished look in {context.format_name}, person first.

## Frame 4 - Poll
Question: {context.cta}
Poll option A: Alltag
Poll option B: Perspektive
"""
