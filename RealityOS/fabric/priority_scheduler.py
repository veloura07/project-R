import heapq
import uuid
import time
from typing import List, Tuple, Callable
from RealityOS.kernel.event_engine import Event

class PriorityScheduler:
    """
    Schedules and dispatches events based on priority.
    Uses a priority queue (heapq) to manage asynchronous computations.
    """
    def __init__(self):
        # elements: Tuple[priority_score, counter, event]
        self._queue: List[Tuple[float, int, Event]] = []
        self._counter = 0

    def schedule(self, event: Event):
        """
        Pushes event to scheduler. Heapq in python is a min-heap,
        so we push negative priority to make it a max-priority queue.
        """
        self._counter += 1
        heapq.heappush(self._queue, (-event.priority, self._counter, event))

    def has_events(self) -> bool:
        return len(self._queue) > 0

    def pop_next(self) -> Event:
        if not self._queue:
            raise IndexError("pop from empty scheduler queue")
        _, _, event = heapq.heappop(self._queue)
        return event

    def clear(self):
        self._queue.clear()
        self._counter = 0

    def size(self) -> int:
        return len(self._queue)
