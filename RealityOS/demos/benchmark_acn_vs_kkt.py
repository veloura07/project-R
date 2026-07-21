"""
benchmark_acn_vs_kkt.py — Comparative Benchmark for Centralized KKT vs ACN.
Simulates a local coordinate perturbation on a large 40-node ring structure.
"""

import math
import copy
from RealityOS import State, Universe

def create_ring_universe(size: int = 40, r: float = 10.0) -> Universe:
    universe = Universe(eta=0.08, alpha_dual=0.05)
    
    # 1. Place nodes in a circle
    gt_coords = []
    for i in range(size):
        angle = 2.0 * math.pi * i / size
        gt_coords.append([r * math.cos(angle), r * math.sin(angle)])
        
    for i in range(size):
        node = universe.create_state(name=f"node_{i}", dim=2)
        node.coords = gt_coords[i]
        
    universe.initialize()
    
    # 2. Apply rigid adjacent distance constraints
    expected_dist = math.sqrt(
        (gt_coords[0][0] - gt_coords[1][0])**2 +
        (gt_coords[0][1] - gt_coords[1][1])**2
    )
    
    def make_tether_constraint(idx_a: int, idx_b: int, dist_val: float):
        return lambda G: math.sqrt((G[idx_a][0] - G[idx_b][0])**2 + (G[idx_a][1] - G[idx_b][1])**2) - dist_val
        
    for i in range(size):
        next_i = (i + 1) % size
        # Use default args in lambda to bind indices properly
        universe.apply_constraint(
            f"tether_{i}_{next_i}",
            make_tether_constraint(i, next_i, expected_dist)
        )
        
    return universe

def main():
    size = 40
    steps = 40
    dt = 0.1
    
    print("============================================================")
    # Highlight the philosophy
    print("  RESEARCH BENCHMARK: CENTRALIZED KKT VS. DECENTRALIZED ACN  ")
    print("============================================================")
    print(f"Network Size: {size} nodes connected in a circular ring.")
    print("Perturbation: Node 0 is pushed outwards by an external goal force.")
    print("Measuring: Coordinate convergence vs. computational updates.")
    print("============================================================\n")
    
    # -------------------------------------------------------------------------
    # CONDITION 1: CENTRALIZED KKT SOLVER (Baseline)
    # -------------------------------------------------------------------------
    universe_kkt = create_ring_universe(size=size)
    universe_kkt.use_negotiation = False
    
    # Apply goal force pushing node 0 outward
    universe_kkt.state_map["node_0"].goal([3.0, 3.0])
    
    kkt_steps_to_converge = None
    kkt_max_violation = 0.0
    
    print("Running Centralized KKT Solver...")
    for step in range(1, steps + 1):
        universe_kkt.step(dt)
        
        # Check max constraint violation
        violations = [abs(c_fn(universe_kkt.engine.G)) for c_fn in universe_kkt.engine.constraints.values()]
        max_v = max(violations) if violations else 0.0
        
        # After first few steps, release the goal force so coordinates can settle
        if step == 5:
            universe_kkt.state_map["node_0"].goal([0.0, 0.0])
            
        if max_v < 0.02 and kkt_steps_to_converge is None and step > 5:
            kkt_steps_to_converge = step
            
        kkt_max_violation = max_v
        
    # Centralized KKT computes updates for ALL nodes at EVERY step
    kkt_total_updates = size * steps
    
    print(f" -> Centralized KKT: Max final violation = {kkt_max_violation:.5f}")
    print(f" -> Centralized KKT: Total updates computed = {kkt_total_updates}\n")
    
    # -------------------------------------------------------------------------
    # CONDITION 2: DECENTRALIZED ACTIVE CONSTRAINT NEGOTIATION (ACN)
    # -------------------------------------------------------------------------
    universe_acn = create_ring_universe(size=size)
    universe_acn.use_negotiation = True
    
    # Start with nodes asleep except Node 0, Node 1, and Node 39 which we perturb
    # (Though the cascade will wake them up dynamically!)
    # Let's initialize all nodes to asleep to prove that cascade wakes them up!
    for i in range(size):
        universe_acn.engine.node_active[i] = False
        universe_acn.engine.node_sleep_ticks[i] = 5
        
    # Apply goal force pushing node 0
    universe_acn.state_map["node_0"].goal([3.0, 3.0])
    
    acn_steps_to_converge = None
    acn_max_violation = 0.0
    
    # Log active nodes at step 6 (right after goal release) to show localized cascade
    active_nodes_log = []
    
    print("Running Decentralized ACN Solver (with sleep cascades)...")
    for step in range(1, steps + 1):
        universe_acn.step(dt)
        
        violations = [abs(c_fn(universe_acn.engine.G)) for c_fn in universe_acn.engine.constraints.values()]
        max_v = max(violations) if violations else 0.0
        
        # Release goal force at step 5
        if step == 5:
            universe_acn.state_map["node_0"].goal([0.0, 0.0])
            
        if max_v < 0.02 and acn_steps_to_converge is None and step > 5:
            acn_steps_to_converge = step
            
        acn_max_violation = max_v
        
        # Track active nodes count
        active_count = sum(1 for active in universe_acn.engine.node_active if active)
        active_nodes_log.append((step, active_count))
        
    acn_total_updates = universe_acn.engine.update_count
    
    print(f" -> Decentralized ACN: Max final violation = {acn_max_violation:.5f}")
    print(f" -> Decentralized ACN: Total updates computed = {acn_total_updates}\n")
    
    # -------------------------------------------------------------------------
    # PRINT RESULTS COMPARISON
    # -------------------------------------------------------------------------
    reduction = (1.0 - (acn_total_updates / kkt_total_updates)) * 100.0
    
    print("============================================================")
    print("                     BENCHMARK COMPARISON                    ")
    print("============================================================")
    print(f"Solver Method            | Updates Computed | Final Violation")
    print(f"-------------------------+------------------+----------------")
    print(f"Centralized KKT Solver   | {kkt_total_updates:<16} | {kkt_max_violation:.5f}")
    print(f"Decentralized ACN Solver | {acn_total_updates:<16} | {acn_max_violation:.5f}")
    print(f"-------------------------+------------------+----------------")
    print(f"COMPUTATIONAL REDUCTION:   {reduction:.2f}% fewer coordinate calculations")
    print("============================================================\n")
    
    print("Trace of Active Nodes per step under Decentralized ACN:")
    print("Step | Active Nodes Count | Status")
    print("-----+--------------------+-----------------------------")
    for step, count in active_nodes_log:
        status_str = "Quiet (Silence)" if count == 0 else ("Perturbation applied" if step <= 5 else "Resolving Cascade")
        print(f"{step:<4} | {count:<18} | {status_str}")
        
    print("\nBenchmark successfully complete.")
    
if __name__ == "__main__":
    main()
