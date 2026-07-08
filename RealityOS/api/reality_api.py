import uuid
from typing import Any, List, Dict
from RealityOS.fabric.cognitive_fabric import CognitiveFabric
from RealityOS.kernel.reality_atom import RealityAtom, Geometry3D
from RealityOS.kernel.event_engine import Event, EventType, StateDelta

class RealityAPI:
    """
    The developer-facing API for RealityOS.
    Bridges application commands into the Cognitive Fabric.
    """
    def __init__(self, fabric: CognitiveFabric):
        self.fabric = fabric

    def observe(self, semantic_type: str, state: List[float], geometry: Geometry3D = None) -> uuid.UUID:
        """Register a new physical observation / atom in the world."""
        atom = RealityAtom(semantic_type=semantic_type, state=state, geometry=geometry)
        self.fabric.register_atom(atom)
        return atom.id

    def execute(self, action_name: str, target: uuid.UUID, delta_vector: List[float]) -> uuid.UUID:
        """Trigger an action event in the environment."""
        event = Event(
            event_type=EventType.EXTERNAL_ACTION,
            target=target,
            delta=StateDelta(delta_vector=delta_vector, magnitude=sum(abs(x) for x in delta_vector))
        )
        self.fabric.event_engine.emit(event)
        return event.id

    def query(self, atom_id: uuid.UUID) -> Dict[str, Any]:
        """Query the state and metadata of a specific atom."""
        atom = self.fabric.atoms.get(atom_id)
        if not atom:
            return {"error": "Atom not found"}
        return {
            "id": atom.id,
            "semantic_type": atom.semantic_type,
            "state": atom.state,
            "energy": atom.energy,
            "confidence": atom.confidence,
            "fields": [str(f) for f in atom.fields]
        }

    def predict(self, atom_id: uuid.UUID, horizon: float) -> List[Any]:
        """Query future states predicted by registered runtimes."""
        # Query predictions from planning and physics runtimes
        # Currently returns empty placeholder
        return []

    def simulate(self, atom_id: uuid.UUID, action_event: Event) -> List[Any]:
        """Pearl do-calculus simulation rollout."""
        return self.fabric.causal_engine.intervene(atom_id, action_event)
        
    def tick(self):
        """Tick the underlying fabric."""
        self.fabric.process_tick()

    def run_loop(self):
        """Processes all queued events until idle."""
        self.fabric.run_until_idle()
