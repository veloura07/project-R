import uuid
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Set, Dict, Optional, List
from RealityOS.kernel.reality_atom import Timestamp, Geometry3D
from RealityOS.kernel.event_engine import Event, EventType

class FieldType(Enum):
    SPATIAL = "spatial"
    SEMANTIC = "semantic"
    CAUSAL = "causal"
    TASK = "task"
    AGENT = "agent"

@dataclass
class LocalityField:
    """A computational neighborhood. Replaces attention windows."""
    
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    field_type: FieldType = FieldType.SPATIAL
    name: str = "Unnamed Field"
    
    members: Set[uuid.UUID] = field(default_factory=set)             # AtomIDs in this field
    boundary: Optional[Geometry3D] = None   # Spatial extent (if spatial field)
    
    # Coupling to other fields
    adjacent_fields: Dict[uuid.UUID, float] = field(default_factory=dict)  # FieldID -> coupling strength [0, 1]
    
    # Activity
    is_active: bool = False                  # Is any member currently changing?
    last_event: Timestamp = field(default_factory=time.time)            # When last computation occurred
    energy: float = 100.0                    # Total computational budget
    
    # Hierarchical
    parent_field: Optional[uuid.UUID] = None  # Containment hierarchy
    child_fields: Set[uuid.UUID] = field(default_factory=set)
    
    def add_member(self, atom_id: uuid.UUID):
        self.members.add(atom_id)
        
    def remove_member(self, atom_id: uuid.UUID):
        if atom_id in self.members:
            self.members.remove(atom_id)

    def propagate(self, event: Event) -> List[Event]:
        """Propagate an event within this field.
        
        Complexity: O(|members|) — NOT O(|members|²)
        This is the key advantage over attention.
        """
        self.last_event = time.time()
        self.is_active = True
        
        propagated_events = []
        for member_id in self.members:
            if member_id == event.target:
                continue # Don't propagate to self
                
            # Attenuate based on some metric (e.g., spatial distance or semantic relevance)
            # In a real implementation, we'd use a relevance function
            relevance = 0.8 
            
            propagated_events.append(
                Event(
                    event_type=EventType.FIELD_UPDATE,
                    source=event.target,
                    target=member_id,
                    delta=event.delta, # Need an attenuate(event.delta, distance) here
                    priority=event.priority * relevance,
                    causal_chain=event.causal_chain + [event.id]
                )
            )
            
        return propagated_events

class FieldManager:
    """Manages all Locality Fields."""
    def __init__(self):
        self.fields: Dict[uuid.UUID, LocalityField] = {}
        
    def create_field(self, name: str, field_type: FieldType) -> LocalityField:
        f = LocalityField(name=name, field_type=field_type)
        self.fields[f.id] = f
        return f
        
    def route_event(self, event: Event, affected_fields: List[uuid.UUID]) -> List[Event]:
        all_new_events = []
        for f_id in affected_fields:
            if f_id in self.fields:
                all_new_events.extend(self.fields[f_id].propagate(event))
        return all_new_events
