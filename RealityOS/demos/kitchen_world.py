import uuid
import time
from RealityOS.kernel.reality_atom import RealityAtom, Geometry3D
from RealityOS.kernel.event_engine import EventEngine, Event, EventType, StateDelta
from RealityOS.kernel.state_transition import StateTransitionNetwork, TransitionFunction, Constraint
from RealityOS.kernel.locality_field import FieldManager, FieldType
from RealityOS.kernel.relation_engine import RelationEngine

# --- A specific physical constraint for our demo ---
class PhysicsConstraint(Constraint):
    def check(self, state, event):
        # Example: z position (index 2) cannot be negative
        if len(state) >= 3 and state[2] < 0:
            print(f"  [PhysicsConstraint] State rejected! z={state[2]} is below floor.")
            return False
        return True

# --- Main Demo ---
def run_kitchen_world():
    print("=== RealityOS: Kitchen World Demo ===")
    
    # 1. Initialize Subsystems
    event_engine = EventEngine()
    stn = StateTransitionNetwork()
    stn.add_constraint(PhysicsConstraint())
    field_manager = FieldManager()
    relation_engine = RelationEngine()
    
    # 2. Setup the World
    print("\nSetting up reality...")
    
    # Create a locality field for the kitchen
    kitchen_field = field_manager.create_field("Kitchen", FieldType.SPATIAL)
    
    # Create Objects (Reality Atoms)
    table = RealityAtom(semantic_type="table", state=[0.0, 0.0, 0.0]) # x, y, z
    cup = RealityAtom(semantic_type="cup", state=[0.0, 0.0, 1.0])    # On the table
    robot_arm = RealityAtom(semantic_type="robot_arm", state=[1.0, 0.0, 1.0])
    
    relation_engine.register_atom(table)
    relation_engine.register_atom(cup)
    relation_engine.register_atom(robot_arm)
    
    # Define relationships
    relation_engine.add_relation(cup.id, table.id, "supported_by")
    relation_engine.add_relation(robot_arm.id, cup.id, "can_reach")
    
    # Add to field
    kitchen_field.add_member(table.id)
    kitchen_field.add_member(cup.id)
    kitchen_field.add_member(robot_arm.id)
    cup.fields.add(kitchen_field.id)
    
    # 3. Simulate an Event (Robot hits the cup)
    print("\nSimulating: Robot arm hits the cup")
    
    # The event: applying a force delta to the cup's state
    # Let's say state is [x, y, z]. We hit it so x increases, and it falls so z decreases.
    hit_event = Event(
        event_type=EventType.EXTERNAL_ACTION,
        source=robot_arm.id,
        target=cup.id,
        delta=StateDelta(delta_vector=[0.5, 0.0, -1.2], magnitude=1.3) # Move x by 0.5, z by -1.2
    )
    
    print(f"Cup initial state: {cup.state}")
    
    # Process through STN
    # The STN processes the event, updates the atom's state if valid, and returns cascading events.
    cascade_events = stn.process_transition(cup, hit_event)
    
    print(f"Cup state after hit attempt: {cup.state}")
    
    # Let's try a smaller hit that doesn't violate physics
    print("\nSimulating: Robot arm nudges the cup gently")
    nudge_event = Event(
        event_type=EventType.EXTERNAL_ACTION,
        source=robot_arm.id,
        target=cup.id,
        delta=StateDelta(delta_vector=[0.1, 0.0, 0.0], magnitude=0.1) # Just move x
    )
    
    cascade_events = stn.process_transition(cup, nudge_event)
    
    print(f"Cup state after nudge: {cup.state}")
    
    # Let's see what cascade events were generated
    print(f"\nCascading events generated: {len(cascade_events)}")
    for ev in cascade_events:
        print(f"  Event: {ev.event_type.name} to target {ev.target}")

    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    run_kitchen_world()
