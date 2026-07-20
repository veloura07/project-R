"""
demo_state_computing.py — Demonstrating the Developer SDK for State Computing.
Shows coordinate evolution, intent goals, counterfactual simulation,
interventions, forks, rewinds, and replays.
"""

import math
from RealityOS import State, Universe

def print_universe(universe: Universe):
    c1 = universe.state_map["drone_1"].coords
    c2 = universe.state_map["drone_2"].coords
    dist = math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)
    print(f"   drone_1: [{c1[0]:.3f}, {c1[1]:.3f}] | drone_2: [{c2[0]:.3f}, {c2[1]:.3f}] | Distance: {dist:.3f}")

def main():
    print("==========================================================")
    print("         REALITYOS: STATE COMPUTING SDK DEMO              ")
    print("==========================================================")
    
    # 1. Initialize a shared Universe
    universe = Universe(eta=0.08, alpha_dual=0.1)
    
    # 2. Create state objects using the factory method
    drone_1 = universe.create_state(name="drone_1", dim=2)
    drone_2 = universe.create_state(name="drone_2", dim=2)
    
    # Set coordinates
    drone_1.coords = [0.0, 0.0]
    drone_2.coords = [2.0, 0.0]
    
    universe.initialize()
    
    # Apply distance constraint (tether limit = 2.5)
    def tether_constraint(G: list) -> float:
        dist = math.sqrt((G[0][0] - G[1][0])**2 + (G[0][1] - G[1][1])**2)
        return dist - 2.5
    universe.apply_constraint("tether", tether_constraint)
    
    print("\nInitial State:")
    print_universe(universe)
    
    # 3. Simulate future projections (Counterfactual Branching)
    # Developers can predict future coordinate trajectories on a forked copy
    # without modifying the active timeline coordinates.
    print("\n[API Call] universe.simulate(steps=3)...")
    drone_2.goal([1.0, 0.0])  # Apply goal force in +X direction
    future_trajectory = universe.simulate(steps=3)
    for idx, G_t in enumerate(future_trajectory, 1):
        dist = math.sqrt((G_t[0][0] - G_t[1][0])**2 + (G_t[0][1] - G_t[1][1])**2)
        print(f" ├─ Step {idx} Projection -> drone_1: [{G_t[0][0]:.3f}, {G_t[0][1]:.3f}] | drone_2: [{G_t[1][0]:.3f}, {G_t[1][1]:.3f}] | Dist: {dist:.3f}")
        
    print("\nActive Timeline Coordinates (unchanged by simulation):")
    print_universe(universe)
    
    # 4. Fork the universe to test a separate dynamic hypothesis
    print("\n[API Call] universe_fork = universe.fork()...")
    universe_fork = universe.fork()
    print("Flipped goal on forked timeline: drone_2 goal force = [-1.0, 0.0]")
    universe_fork.state_map["drone_2"].goal([-1.0, 0.0])
    
    print("Stepping forked universe...")
    universe_fork.step()
    print(" Forked State:")
    print_universe(universe_fork)
    
    print(" Active Timeline State (untouched by fork):")
    print_universe(universe)
    
    # 5. Intervene on the active timeline coordinates
    # Directly injects an external perturbation impulse to coordinates.
    print("\n[API Call] drone_1.intervene([-1.0, -1.0]) (moving drone_1)...")
    drone_1.intervene([-1.0, -1.0])
    print_universe(universe)
    
    # Evolve the active timeline for a few ticks
    print("\nStepping active universe (3 ticks)...")
    for tick in range(1, 4):
        universe.step()
        print(f" Tick {tick}:")
        print_universe(universe)
        
    # 6. Rewind the active timeline (Time-Travel Debugging)
    # Rolls back the coordinate state G to a historical trajectory step.
    print("\n[API Call] universe.rewind(steps=2)...")
    universe.rewind(2)
    print("Active Timeline (Rewound 2 steps):")
    print_universe(universe)
    
    # 7. Replay a trajectory
    # Replays a specific sequence of coordinate matrices.
    print("\n[API Call] universe.replay(future_trajectory)...")
    def replay_callback(u):
        print_universe(u)
    universe.replay(future_trajectory, tick_callback=replay_callback)
    
    print("\n==========================================================")
    print("             DEMO COMPLETED SUCCESSFULLY                  ")
    print("==========================================================")

if __name__ == "__main__":
    main()
