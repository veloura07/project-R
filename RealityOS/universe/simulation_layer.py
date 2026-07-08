import uuid
from typing import Dict, List, Tuple, Any
from RealityOS.kernel.reality_atom import RealityAtom
from RealityOS.kernel.event_engine import Event

class SimulationSandbox:
    """
    An isolated world state partition to run 'what-if' simulations.
    Clones the atoms and executes state updates locally.
    """
    def __init__(self, original_atoms: Dict[uuid.UUID, RealityAtom]):
        self.atoms: Dict[uuid.UUID, RealityAtom] = {}
        for atom_id, atom in original_atoms.items():
            # Clone atom properties, state vectors, relations
            cloned = RealityAtom(
                id=atom.id,
                semantic_type=atom.semantic_type,
                state=atom.state.copy(),
                geometry=atom.geometry,
                confidence=atom.confidence
            )
            # copy relations
            for rel_type, edges in atom.relations.edges.items():
                cloned.relations.edges[rel_type] = edges.copy()
            cloned.properties = atom.properties.copy()
            self.atoms[atom_id] = cloned

    def apply_event(self, event: Event, stn, runtimes: List[Any]):
        """Runs the event inside the cloned sandbox state."""
        target_atom = self.atoms.get(event.target)
        if not target_atom:
            return []

        # Process via STN
        cascade = stn.process_transition(target_atom, event)
        
        # Route to runtimes inside this sandbox
        for rt in runtimes:
            if rt.accepts(event):
                cascade.extend(rt.process(event, self.atoms))
                
        return cascade

class SimulationLayer:
    """
    Coordinates spawning sandbox rollouts to predict potential futures.
    Used for planning validation and collision forecasting.
    """
    def __init__(self, stn, runtimes: List[Any]):
        self.stn = stn
        self.runtimes = runtimes

    def spawn_simulation(self, original_atoms: Dict[uuid.UUID, RealityAtom]) -> SimulationSandbox:
        return SimulationSandbox(original_atoms)

    def forecast_rollout(self, original_atoms: Dict[uuid.UUID, RealityAtom], seed_event: Event, steps: int = 5) -> Dict[uuid.UUID, List[float]]:
        """Runs a forward simulation and returns the resulting states."""
        sandbox = self.spawn_simulation(original_atoms)
        events = [seed_event]
        
        for _ in range(steps):
            next_events = []
            for ev in events:
                next_events.extend(sandbox.apply_event(ev, self.stn, self.runtimes))
            events = next_events
            if not events:
                break
                
        # Return mapped final states
        return {atom_id: atom.state.copy() for atom_id, atom in sandbox.atoms.items()}
