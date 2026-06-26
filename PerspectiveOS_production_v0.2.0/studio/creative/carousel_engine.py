try:
    from ..brain.index import IndexedKnowledge
    from .context import CreativeContextBuilder, CreativeInputs
except ImportError:
    from brain.index import IndexedKnowledge
    from creative.context import CreativeContextBuilder, CreativeInputs


class CarouselEngine:
    """Generates a six-slide carousel concept from repository knowledge."""

    def __init__(self, knowledge: IndexedKnowledge) -> None:
        """Create a carousel engine bound to the current KnowledgeIndex."""
        self.knowledge = knowledge

    def generate(self, inputs: CreativeInputs) -> str:
        """Generate a six-slide carousel structure."""
        context = CreativeContextBuilder(self.knowledge).build(inputs)
        return f"""# Carousel

## Format
{context.format_name}

## Slide 1 - Hook
Text: {context.hook}
Visual: {context.scene}

## Slide 2 - Problem
Text: Viele sehen zuerst {context.aid_visibility}. Der Rest der Situation wird kleiner.
Visual: Natural smartphone look at {context.location}.

## Slide 3 - Perspective
Text: {context.metaphor_line}
Visual: Calm detail with enough safe margin and little text.

## Slide 4 - Personal Moment
Text: Ich bin nicht unterwegs, um etwas zu beweisen. Ich bin einfach unterwegs.
Visual: {context.outfit}, natural posture, person first.

## Slide 5 - Takeaway
Text: {context.perspective_sentence}
Visual: Warm ending image, no over-staging.

## Slide 6 - CTA
Text: {context.cta}
Visual: Open, community-facing final frame.

## Design Guardrails
{context.format_rules}; {context.layout_rules}
"""
