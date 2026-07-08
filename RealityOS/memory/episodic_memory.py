import uuid
from typing import List, Tuple
from RealityOS.kernel.event_engine import Event

class EpisodicMemory:
    """
    Episodic Memory stores specific event occurrences with their full context.
    Bounded capacity ring buffer. Auto-compresses over time.
    """
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.episodes: List[Event] = []

    def record_episode(self, event: Event):
        self.episodes.append(event)
        if len(self.episodes) > self.capacity:
            # Drop oldest episode. In a production system, this triggers
            # consolidation to Semantic memory.
            self.episodes.pop(0)

    def search_episodes(self, query_type: str) -> List[Event]:
        # Return occurrences matching some basic filter
        return [e for e in self.episodes if e.event_type.value == query_type]
