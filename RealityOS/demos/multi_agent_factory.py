"""
multi_agent_factory.py — Multi-Agent Factory Simulation Demo.
Demonstrates the full RealityOS stack: Multi-Agent Beliefs, Belief Sync,
Online Rule Learning, and the Multi-Timescale Brain.
"""

import uuid
import time
from RealityOS.kernel.cognitive_state import CognitiveState, Evidence, Constraint
from RealityOS.kernel.reality_atom import RealityAtom, Geometry3D
from RealityOS.kernel.event_engine import Event, EventType, StateDelta
from RealityOS.kernel.cognitive_field import CognitiveField2D
from RealityOS.fabric.cognitive_fabric import CognitiveFabric
from RealityOS.fabric.belief_synchronizer import BeliefSynchronizer, SyncStrategy
from RealityOS.universe.belief_layer import BeliefLayer
from RealityOS.runtimes.physics_runtime import PhysicsRuntime
from RealityOS.runtimes.planning_runtime import PlanningRuntime
from RealityOS.runtimes.learning_runtime import LearningRuntime
from RealityOS.memory.semantic_memory import SemanticMemory
from RealityOS.fabric.multi_timescale_brain import MultiTimescaleBrain


def run_factory_demo():
    print("==================================================")
    print("    AION / RealityOS: MULTI-AGENT FACTORY DEMO     ")
    print("==================================================")

    # 1. Initialize core fabric and layers
    fabric = CognitiveFabric()
    belief_layer = BeliefLayer()
    belief_sync = BeliefSynchronizer(belief_layer)
    semantic_mem = SemanticMemory()

    # 2. Register runtimes
    physics_rt = PhysicsRuntime()
    planning_rt = PlanningRuntime()
    learning_rt = LearningRuntime(semantic_mem)
    fabric.register_runtime(physics_rt)
    fabric.register_runtime(planning_rt)
    fabric.register_runtime(learning_rt)

    # 3. Create Multi-Agent Belief Models
    # We have two robot agents working in the warehouse
    robot_alpha_id = uuid.uuid4()
    robot_beta_id = uuid.uuid4()
    
    agent_a = belief_layer.register_agent(robot_alpha_id, "Robot_Alpha")
    agent_b = belief_layer.register_agent(robot_beta_id, "Robot_Beta")

    # 4. Instantiation of a shared physical target atom (e.g. a toolbox)
    toolbox = RealityAtom(
        semantic_type="toolbox",
        state=[1.0, 1.0, 0.0],
        geometry=Geometry3D(x=1.0, y=1.0, z=0.0, volume=0.5)
    )
    fabric.register_atom(toolbox)

    # 5. Divergent Beliefs Setup
    # Robot Alpha observes the toolbox closely (low variance)
    agent_a.observe(
        atom_id=toolbox.id,
        observed_state=[1.02, 0.98, 0.0],
        observation_variance=[0.01, 0.01, 0.01]
    )

    # Robot Beta observes the toolbox from far away (high variance, different position estimate)
    agent_b.observe(
        atom_id=toolbox.id,
        observed_state=[1.30, 0.85, 0.0],
        observation_variance=[0.15, 0.15, 0.15]
    )

    print("\n--- Initial Divergent Subjective Realities ---")
    print(f"Robot Alpha belief of toolbox: {[round(x, 3) for x in agent_a.get_believed_state(toolbox.id)]}")
    print(f"Robot Beta belief of toolbox:  {[round(x, 3) for x in agent_b.get_believed_state(toolbox.id)]}")
    
    disagreement = agent_a.divergence_from(agent_b, toolbox.id)
    print(f"Subjective divergence index: {disagreement:.3f}")

    # Synchronize their beliefs via SENSOR_FUSION (Kalman merge)
    print("\n--- Synchronizing Agent Beliefs via Kalman Sensor Fusion ---")
    sync_res = belief_sync.sync_agents(robot_alpha_id, robot_beta_id, toolbox.id, SyncStrategy.SENSOR_FUSION)
    print(f"Merged consensus belief: {[round(x, 3) for x in sync_res.merged_state]}")
    print(f"Robot Alpha new belief: {[round(x, 3) for x in agent_a.get_believed_state(toolbox.id)]}")
    print(f"Robot Beta new belief:  {[round(x, 3) for x in agent_b.get_believed_state(toolbox.id)]}")

    # 6. Initialize Cognitive State for Evolution Loops
    # We instantiate a CognitiveState representing warehouse safety coordinates
    # We set a boundary constraint: y coordinate cannot be negative
    safety_boundary = Constraint(
        name="Safety Wall Boundary",
        violation_fn=lambda pos: max(0.0, -pos[1]) ** 2
    )
    
    cs = CognitiveState(uid="safety_target", x=[1.0, 1.0], value=0.9, type_tag="safety_zone")
    cs.constraints.append(safety_boundary)
    
    # Pulled toward attractor [1.0, -0.5] (behind safety wall)
    cs.g = [0.0, -1.0] 
    fabric.register_cognitive_state(cs)

    # 7. Setup Cognitive Field
    risk_field = CognitiveField2D("Warehouse_Risk", width=10, height=10, dx=1.0)
    fabric.field_manager.fields[uuid.uuid4()] = risk_field

    # 8. Setup Multi-Timescale Brain loops
    print("\n--- Starting Multi-Timescale Brain Execution Loop ---")
    brain = MultiTimescaleBrain(fabric)

    # Simulate 20 ticks of virtual time
    t_start = time.time()
    for tick in range(1, 21):
        # We step time virtualized to force loops to run in succession
        t_virtual = t_start + tick * 0.1
        
        # Periodic observation logs ingested into the learning buffer
        obs_event = Event(
            event_type=EventType.SENSOR_OBSERVATION,
            target=cs.uid,
            delta=StateDelta(delta_vector=[0.05, -0.05], magnitude=0.07)
        )
        fabric.register_atom(RealityAtom(id=cs.uid, semantic_type="safety_zone", state=cs.x))
        fabric.event_engine.emit(obs_event)

        # Tick the brain loops
        brain.tick(custom_time=t_virtual)
        
        # Drain scheduled priority queue
        fabric.run_until_idle(timeout_steps=5)

        if tick % 4 == 0:
            print(f"Tick {tick:02d} | Zone Pos: {[round(v, 3) for v in cs.x]} | Surprise: {cs.meta['surprise']:.4f} | Energy: {cs.energy_budget:.3f}")

    print("\n--- Final Consolidated Semantic Knowledge ---")
    # Verify if invariant bounds were successfully extracted and compiled by the Learning Runtime
    compiled_rule = semantic_mem.query_fact("safety_zone", "invariant_bounds")
    if compiled_rule:
        print(f"Compiled Safety Zone Invariant Boundary:")
        print(f"  Dimension: {compiled_rule['dimension']}")
        print(f"  Bounds: [{compiled_rule['lower']:.3f}, {compiled_rule['upper']:.3f}]")
    else:
        print("No rules compiled yet. Buffering snapshots...")

    print("==================================================")
    print("      Factory Demo Completed Successfully         ")
    print("==================================================")


if __name__ == "__main__":
    run_factory_demo()
