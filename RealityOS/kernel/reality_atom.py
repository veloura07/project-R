import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
import time

# --- Placeholder types for type hinting and structural completeness ---
StateVector = List[float]
Timestamp = float

@dataclass
class Property:
    name: str
    value: Any
    type_str: str

@dataclass
class Geometry3D:
    # Simplified placeholder for spatial geometry
    x: float
    y: float
    z: float
    volume: float = 0.0

@dataclass
class BeliefDistribution:
    # Placeholder for P(state | evidence)
    mean: StateVector
    variance: StateVector

@dataclass
class SparseRelationMap:
    # typed edges: relation_type -> Set[AtomID]
    edges: Dict[str, Set[uuid.UUID]] = field(default_factory=dict)

@dataclass
class Future:
    predicted_state: StateVector
    probability: float
    time_horizon: float

@dataclass
class StateSnapshot:
    state: StateVector
    timestamp: Timestamp

class RingBuffer:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer: List[StateSnapshot] = []
        self.head = 0

    def append(self, item: StateSnapshot):
        if len(self.buffer) < self.capacity:
            self.buffer.append(item)
        else:
            self.buffer[self.head] = item
            self.head = (self.head + 1) % self.capacity

    def get_latest(self) -> Optional[StateSnapshot]:
        if not self.buffer:
            return None
        idx = (self.head - 1) % len(self.buffer)
        return self.buffer[idx]


# --- The Reality Atom ---

@dataclass
class RealityAtom:
    """The fundamental computational primitive of RealityOS.
    
    Replaces: tokens (LLMs), patches (ViTs), embeddings (all models)
    Complexity: O(1) per atom, O(k) per update where k = neighbor count
    """
    # === Identity (Immutable) ===
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    semantic_type: str = "unknown"
    created_at: Timestamp = field(default_factory=time.time)
    
    # === State (Mutable, versioned) ===
    state: StateVector = field(default_factory=list)
    properties: Dict[str, Property] = field(default_factory=dict)
    geometry: Optional[Geometry3D] = None
    
    # === Uncertainty (Bayesian) ===
    belief: Optional[BeliefDistribution] = None
    confidence: float = 1.0                # [0, 1] — how certain we are this exists
    evidence_count: int = 0                # How many observations support this
    last_observed: Timestamp = field(default_factory=time.time)
    
    # === Relational ===
    relations: SparseRelationMap = field(default_factory=SparseRelationMap)
    fields: Set[uuid.UUID] = field(default_factory=set) # FieldIDs
    parent: Optional[uuid.UUID] = None           # Hierarchical containment
    children: Set[uuid.UUID] = field(default_factory=set)
    
    # === Temporal ===
    history: RingBuffer = field(default_factory=lambda: RingBuffer(100))
    velocity: StateVector = field(default_factory=list)  # Rate of state change
    predicted_futures: List[Future] = field(default_factory=list)
    
    # === Metabolism ===
    energy: float = 1.0                     # Computational priority / importance
    decay_rate: float = 0.01                # How quickly energy dissipates
    last_active: Timestamp = field(default_factory=time.time)

    def update_state(self, new_state: StateVector, timestamp: Timestamp = None):
        """Updates the state and records history."""
        ts = timestamp or time.time()
        self.history.append(StateSnapshot(state=self.state.copy(), timestamp=ts))
        self.state = new_state
        self.last_active = ts

    def add_relation(self, relation_type: str, target_id: uuid.UUID):
        if relation_type not in self.relations.edges:
            self.relations.edges[relation_type] = set()
        self.relations.edges[relation_type].add(target_id)
