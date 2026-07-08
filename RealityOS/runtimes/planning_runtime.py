import uuid
from typing import List, Any
from RealityOS.runtimes.base_runtime import IntelligenceRuntime
from RealityOS.kernel.event_engine import Event, EventType, StateDelta
from RealityOS.kernel.reality_atom import Future

class PlanningRuntime(IntelligenceRuntime):
    """
    Subclass of IntelligenceRuntime that handles planning goals
    and multi-step task decomposition using causal relationships.
    """
    def __init__(self):
        super().__init__("PlanningRuntime")
        self.active_plans = {}

    def accepts(self, event: Event) -> bool:
        # Accepts task goal definitions or events suggesting a goal is unfulfilled
        return event.event_type in (EventType.EXTERNAL_ACTION, EventType.STATE_TRANSITION)

    def process(self, event: Event, context: Any) -> List[Event]:
        """
        Decomposes a goal state into motor steps and triggers actions.
        """
        atoms = context
        target_atom = atoms.get(event.target)
        if not target_atom:
            return []

        # Check if the target has an active goal property
        if "goal_state" not in target_atom.properties:
            return []

        goal_pos = target_atom.properties["goal_state"].value
        current_pos = target_atom.state[:3]
        
        # Calculate distance to goal
        dist = self._distance(current_pos, goal_pos)
        if dist < 0.1:
            print(f"  [PlanningRuntime] Goal reached for '{target_atom.semantic_type}'!")
            # Remove goal
            del target_atom.properties["goal_state"]
            return []

        print(f"  [PlanningRuntime] Goal mismatch for '{target_atom.semantic_type}': current={current_pos}, goal={goal_pos}. Planning path...")

        # Search causal relations to find an actor
        # Find which robot has 'can_reach' or control capability over target_atom
        actor_id = None
        for atom in atoms.values():
            if "can_reach" in atom.relations.edges:
                if target_atom.id in atom.relations.edges["can_reach"]:
                    actor_id = atom.id
                    break

        if not actor_id:
            print(f"  [PlanningRuntime] No actor found that can interact with '{target_atom.semantic_type}'. Planning aborted.")
            return []

        actor_atom = atoms[actor_id]
        print(f"  [PlanningRuntime] Found actor: '{actor_atom.semantic_type}' ({actor_id})")

        # Causal decomposition plan:
        # Step 1: If actor is far from target, move actor closer to target
        # Step 2: Grab / shift target towards goal
        actor_pos = actor_atom.state[:3]
        dist_actor_to_target = self._distance(actor_pos, current_pos)
        
        cascade_events = []
        if dist_actor_to_target > 0.2:
            # Move actor closer to target
            print(f"  [PlanningRuntime] Causal Step 1: Move actor closer to target. Distance: {dist_actor_to_target:.2f}")
            # Target is the actor itself
            move_delta = [current_pos[i] - actor_pos[i] for i in range(3)]
            # normalize and scale
            move_delta = [d * 0.5 for d in move_delta]
            move_ev = Event(
                event_type=EventType.EXTERNAL_ACTION,
                source=self.name,
                target=actor_id,
                delta=StateDelta(delta_vector=move_delta, magnitude=0.5)
            )
            cascade_events.append(move_ev)
        else:
            # Shift target towards goal
            print(f"  [PlanningRuntime] Causal Step 2: Direct manipulation of target towards goal.")
            push_delta = [goal_pos[i] - current_pos[i] for i in range(3)]
            # clamp push delta
            magnitude = sum(abs(x) for x in push_delta)
            if magnitude > 0.5:
                push_delta = [d * (0.5 / magnitude) for d in push_delta]
            push_ev = Event(
                event_type=EventType.EXTERNAL_ACTION,
                source=actor_id,
                target=target_atom.id,
                delta=StateDelta(delta_vector=push_delta, magnitude=0.5)
            )
            cascade_events.append(push_ev)

        return cascade_events

    def predict(self, atom_id: uuid.UUID, horizon: float) -> List[Future]:
        return []

    def _distance(self, p1: List[float], p2: List[float]) -> float:
        import math
        return math.sqrt(sum((x1 - x2)**2 for x1, x2 in zip(p1, p2)))

