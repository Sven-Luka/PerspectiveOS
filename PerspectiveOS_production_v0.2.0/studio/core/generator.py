try:
    from ..brain.index import IndexedKnowledge
    from ..creative.brief_generator import BriefGenerator, TopicProfile
except ImportError:
    from brain.index import IndexedKnowledge
    from creative.brief_generator import BriefGenerator, TopicProfile


def build_brief(
    topic: str,
    target_emotion: str,
    image_type: str,
    knowledge: IndexedKnowledge,
) -> str:
    """Compatibility wrapper for legacy imports; delegates to BriefGenerator."""
    return BriefGenerator(knowledge).generate(topic, target_emotion, image_type)


__all__ = ["BriefGenerator", "TopicProfile", "build_brief"]
