from abc import ABC, abstractmethod
from typing import List, Any
import uuid
from RealityOS.kernel.event_engine import Event
from RealityOS.kernel.reality_atom import Future

class HealthReport:
    def __init__(self, status: str, details: str):
        self.status = status
        self.details = details

class IntelligenceRuntime(ABC):
    """
    Abstract base class for all Intelligence Runtimes (modules).
    Plugins that connect to the Cognitive Fabric's event loops.
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def accepts(self, event: Event) -> bool:
        """Determines if this runtime should process this event."""
        pass

    @abstractmethod
    def process(self, event: Event, context: Any) -> List[Event]:
        """Process an event and return proposed cascade events."""
        pass

    @abstractmethod
    def predict(self, atom_id: uuid.UUID, horizon: float) -> List[Future]:
        """Predict future states for an atom."""
        pass

    def wake(self):
        print(f"  [Runtime] {self.name} woke up.")

    def sleep(self):
        print(f"  [Runtime] {self.name} fell asleep.")

    def dream(self):
        """Background learning / offline consolidation."""
        print(f"  [Runtime] {self.name} is consolidation dreaming.")

    def health(self) -> HealthReport:
        return HealthReport("OK", "Healthy runtime.")

    def energy_usage(self) -> float:
        return 0.1
