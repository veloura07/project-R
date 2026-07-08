import uuid
from typing import List, Any
from RealityOS.runtimes.base_runtime import IntelligenceRuntime
from RealityOS.kernel.event_engine import Event, EventType, StateDelta
from RealityOS.kernel.reality_atom import Future, RealityAtom, Geometry3D

class PhysicsRuntime(IntelligenceRuntime):
    """
    Subclass of IntelligenceRuntime that handles physical updates,
    gravitational acceleration, motion integration, and collision detection.
    """
    def __init__(self):
        super().__init__("PhysicsRuntime")
        self.gravity = [0.0, 0.0, -9.8] # x, y, z acceleration

    def accepts(self, event: Event) -> bool:
        return event.event_type in (EventType.EXTERNAL_ACTION, EventType.FIELD_UPDATE, EventType.STATE_TRANSITION)

    def process(self, event: Event, context: Any) -> List[Event]:
        """
        Updates the physical state of the target atom based on physics mechanics.
        If the atom is falling, integrates gravity.
        """
        # Context is expected to be a Dict[uuid.UUID, RealityAtom] of the local universe
        atoms = context
        target_atom = atoms.get(event.target)
        if not target_atom or not target_atom.geometry:
            return []

        cascade_events = []
        dt = 0.1 # Simulated time step (100ms)

        # Check if supported by any object
        is_supported = False
        if "supported_by" in target_atom.relations.edges:
            for support_id in target_atom.relations.edges["supported_by"]:
                support_atom = atoms.get(support_id)
                if support_atom:
                    # Table Z + height vs Cup Z
                    # Simple support verification: if the support exists, we assume support
                    is_supported = True
                    break

        # Calculate new velocity
        current_vel = getattr(target_atom, "velocity", [0.0, 0.0, 0.0])
        if len(current_vel) < 3:
            current_vel = [0.0, 0.0, 0.0]

        if not is_supported and target_atom.state[2] > 0.0:
            # Fall due to gravity: v = v + g * dt
            new_vel = [
                current_vel[0] + self.gravity[0] * dt,
                current_vel[1] + self.gravity[1] * dt,
                current_vel[2] + self.gravity[2] * dt
            ]
            print(f"  [PhysicsRuntime] Object '{target_atom.semantic_type}' is falling. Velocity: {new_vel}")
        else:
            new_vel = [0.0, 0.0, 0.0]

        # Integrate motion: x = x + v * dt
        proposed_state = [
            target_atom.state[0] + new_vel[0] * dt,
            target_atom.state[1] + new_vel[1] * dt,
            target_atom.state[2] + new_vel[2] * dt
        ]
        
        # Check collision with other atoms
        for other_id, other_atom in atoms.items():
            if other_id == target_atom.id or not other_atom.geometry:
                continue
            
            # Simple bounding sphere collision check
            dist = self._distance(proposed_state, other_atom.state)
            min_dist = 0.5 # Simplified collision radius
            if dist < min_dist:
                print(f"  [PhysicsRuntime] COLLISION DETECTED between '{target_atom.semantic_type}' and '{other_atom.semantic_type}'!")
                # Zero out downward velocity and halt Z displacement
                new_vel = [0.0, 0.0, 0.0]
                proposed_state[2] = other_atom.state[2] + 0.3 # Place slightly above
                
                # Emit a collision event
                collision_event = Event(
                    event_type=EventType.CASCADE,
                    source=target_atom.id,
                    target=other_id,
                    delta=StateDelta(delta_vector=[0.0, 0.0, 0.0], magnitude=1.0)
                )
                cascade_events.append(collision_event)
                break

        # Save velocity back
        target_atom.velocity = new_vel
        
        # If position changed significantly, update it via transition
        if proposed_state != target_atom.state:
            update_delta = [proposed_state[i] - target_atom.state[i] for i in range(3)]
            state_transition_ev = Event(
                event_type=EventType.STATE_TRANSITION,
                source=self.name,
                target=target_atom.id,
                delta=StateDelta(delta_vector=update_delta, magnitude=sum(abs(x) for x in update_delta))
            )
            cascade_events.append(state_transition_ev)

        return cascade_events

    def predict(self, atom_id: uuid.UUID, horizon: float) -> List[Future]:
        # Return physical trajectory extrapolation
        return []

    def _distance(self, p1: List[float], p2: List[float]) -> float:
        import math
        return math.sqrt(sum((x1 - x2)**2 for x1, x2 in zip(p1, p2)))

