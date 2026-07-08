import uuid
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from RealityOS.kernel.reality_atom import Timestamp, StateVector

class EventType(Enum):
    # External
    SENSOR_OBSERVATION = "sensor_observation"     # New sensory data
    EXTERNAL_ACTION = "external_action"           # Something in world changed
    
    # Internal
    STATE_TRANSITION = "state_transition"          # Atom state update
    RELATION_CHANGE = "relation_change"            # Graph topology change  
    BELIEF_UPDATE = "belief_update"                # Uncertainty changed
    PREDICTION_GENERATED = "prediction_generated"  # Future state predicted
    
    # Propagated
    FIELD_UPDATE = "field_update"                  # Locality field changed
    CASCADE = "cascade"                            # Ripple from another event
    
    # System
    ENERGY_CHANGE = "energy_change"                # Atom importance changed
    GARBAGE_COLLECT = "garbage_collect"            # Atom expired


@dataclass
class StateDelta:
    """Represents a change in state vector."""
    delta_vector: StateVector
    magnitude: float

@dataclass
class Event:
    """The unit of change in RealityOS. Replaces tokens as the input primitive."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp: Timestamp = field(default_factory=time.time)
    event_type: EventType = EventType.INTERNAL
    
    source: Optional[uuid.UUID] = None   # What caused this event
    target: uuid.UUID = field(default_factory=uuid.uuid4) # What this event affects
    
    delta: Optional[StateDelta] = None   # The change being proposed
    
    # Causal provenance
    cause: Optional[uuid.UUID] = None        # What event caused this one
    causal_chain: List[uuid.UUID] = field(default_factory=list) # Full causal history
    
    # Priority and routing
    priority: float = 1.0                # Urgency (affects scheduling)
    propagation_radius: int = 1          # How far this should ripple
    
    # Uncertainty
    probability: float = 1.0             # How likely is this event real
    evidence: List[uuid.UUID] = field(default_factory=list) # Supporting sensor data


class EventBus:
    """The central nervous system for routing events."""
    def __init__(self):
        self.subscribers = []
        self.queue = []

    def publish(self, event: Event):
        self.queue.append(event)
        # In a real system, this would be an async dispatch or handled by a scheduler
        self._dispatch(event)

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def _dispatch(self, event: Event):
        for sub in self.subscribers:
            sub(event)

class EventEngine:
    """Coordinates events and drives the computation in RealityOS."""
    def __init__(self):
        self.bus = EventBus()
        self.event_history: Dict[uuid.UUID, Event] = {}

    def emit(self, event: Event):
        self.event_history[event.id] = event
        self.bus.publish(event)
