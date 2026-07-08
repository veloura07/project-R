import uuid
import time
from RealityOS.kernel.reality_atom import RealityAtom, Geometry3D, Property
from RealityOS.kernel.event_engine import Event, EventType, StateDelta
from RealityOS.fabric.cognitive_fabric import CognitiveFabric
from RealityOS.fabric.energy_manager import EnergyState
from RealityOS.runtimes.physics_runtime import PhysicsRuntime
from RealityOS.runtimes.planning_runtime import PlanningRuntime
from RealityOS.universe.simulation_layer import SimulationLayer
from RealityOS.kernel.world_partition import WorldPartition, PartitionState

def run_robot_manipulation_demo():
    print("==================================================")
    print("   RealityOS: EMBODIED PHYSICAL ROBOTICS DEMO     ")
    print("==================================================")
    
    # 1. Setup Cognitive Fabric
    fabric = CognitiveFabric()
    
    # Register Intelligence Runtimes
    physics_rt = PhysicsRuntime()
    planning_rt = PlanningRuntime()
    fabric.register_runtime(physics_rt)
    fabric.register_runtime(planning_rt)
    
    # 2. Setup the Hierarchical World Partition
    print("\n--- Phase 1: Hierarchical World Partition Setup ---")
    assembly_room = WorldPartition("Assembly Room")
    assembly_room.transition_state(PartitionState.COMPUTING)
    
    # 3. Create & Register Physical Atoms
    print("\n--- Phase 2: Instantiating Reality Atoms ---")
    
    # Robot Arm
    robot_arm = RealityAtom(
        semantic_type="robot_arm", 
        state=[0.0, 0.0, 1.0], # x, y, z
        geometry=Geometry3D(x=0.0, y=0.0, z=1.0, volume=0.1)
    )
    
    # Table (Supporting surface)
    table = RealityAtom(
        semantic_type="table", 
        state=[1.0, 0.0, 0.0], 
        geometry=Geometry3D(x=1.0, y=0.0, z=0.0, volume=1.0)
    )
    
    # Cup (Manipulable target)
    cup = RealityAtom(
        semantic_type="cup", 
        state=[1.0, 0.0, 1.0], 
        geometry=Geometry3D(x=1.0, y=0.0, z=1.0, volume=0.05)
    )
    
    # Obstacle block on the table path
    obstacle = RealityAtom(
        semantic_type="obstacle_block",
        state=[1.5, 0.0, 1.0],
        geometry=Geometry3D(x=1.5, y=0.0, z=1.0, volume=0.2)
    )
    
    # Set relations
    relation_engine = fabric.relation_engine
    
    # Setup initial registration
    fabric.register_atom(robot_arm)
    fabric.register_atom(table)
    fabric.register_atom(cup)
    fabric.register_atom(obstacle)
    
    # Set graph relations
    relation_engine.add_relation(robot_arm.id, cup.id, "can_reach")
    relation_engine.add_relation(cup.id, table.id, "supported_by")
    
    # Add to partition
    assembly_room.add_atom(robot_arm)
    assembly_room.add_atom(table)
    assembly_room.add_atom(cup)
    assembly_room.add_atom(obstacle)

    # Set Goal Property on the Cup: Place at [2.0, 0.0, 1.0] (the other side of table)
    cup.properties["goal_state"] = Property("goal_state", [2.0, 0.0, 1.0], "List[float]")
    
    print(f"Robot Arm initial position: {robot_arm.state}")
    print(f"Cup initial position: {cup.state}")
    print(f"Cup Goal State: {cup.properties['goal_state'].value}")
    print(f"Obstacle positioned at: {obstacle.state}")
    
    # 4. Run the Causal Planning Loop
    print("\n--- Phase 3: Executing Goal-Driven Plan (Ticking Event Loop) ---")
    
    # Trigger planning runtime check by firing a state transition event on the cup
    trigger_event = Event(
        event_type=EventType.STATE_TRANSITION,
        target=cup.id,
        delta=StateDelta(delta_vector=[0.0, 0.0, 0.0], magnitude=0.0)
    )
    fabric.event_engine.emit(trigger_event)
    
    # Run the loop for up to 10 ticks to let the robot move and push the cup
    for tick in range(1, 8):
        print(f"\n[Tick {tick}] Processing scheduled events...")
        fabric.process_tick()
        # Drain cascade queue
        fabric.run_until_idle(timeout_steps=5)
        print(f"  Robot Arm position: {robot_arm.state}")
        print(f"  Cup position: {cup.state}")
        
    # 5. Counterfactual Simulation Rollout
    print("\n--- Phase 4: Counterfactual Simulation ('What If?') ---")
    sim_layer = SimulationLayer(fabric.stn, [physics_rt, planning_rt])
    
    # Sandbox Counterfactual: What if the obstacle wasn't there?
    print("Spawning isolated Sandbox rollout...")
    sandbox_atoms = fabric.atoms.copy()
    # Remove obstacle from sandbox
    if obstacle.id in sandbox_atoms:
        del sandbox_atoms[obstacle.id]
        
    sandbox = sim_layer.spawn_simulation(sandbox_atoms)
    
    # Trigger same nudge/push event in the sandbox
    sim_push_event = Event(
        event_type=EventType.EXTERNAL_ACTION,
        source=robot_arm.id,
        target=cup.id,
        delta=StateDelta(delta_vector=[0.5, 0.0, 0.0], magnitude=0.5)
    )
    
    print("Running sandbox forward simulation rollout...")
    # Inject push event and run sandbox
    sandbox.apply_event(sim_push_event, fabric.stn, [physics_rt])
    
    print(f"  Ground Truth Cup Position (blocked): {cup.state}")
    print(f"  Sandbox Cup Position (if unblocked): {sandbox.atoms[cup.id].state}")
    
    # 6. Memory Virtual Partitions
    print("\n--- Phase 5: Hierarchical Virtual Memory Partitioning ---")
    print(f"Assembly Room initial status: {assembly_room.state.value}")
    print(f"In-memory atoms in Assembly Room: {len(assembly_room.atoms)}")
    
    # Unload Room to simulate persistent storage saving RAM
    assembly_room.transition_state(PartitionState.UNLOADED)
    print(f"Assembly Room status after save: {assembly_room.state.value}")
    print(f"In-memory atoms in Assembly Room: {len(assembly_room.atoms)}")
    
    # Reload room when entering COMPUTING state
    assembly_room.transition_state(PartitionState.COMPUTING)
    print(f"In-memory atoms in Assembly Room after reload: {len(assembly_room.atoms)}")
    
    print("\n==================================================")
    print("            Demo Finished Successfully            ")
    print("==================================================")

if __name__ == "__main__":
    run_robot_manipulation_demo()
