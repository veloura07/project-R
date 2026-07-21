"""
test_acn_solver.py — Automated Unit Tests for Decentralized Active Constraint Negotiation.
Verifies convergence parity with KKT, O(k) update sparsity, and silence gating.
"""

import unittest
import math
from RealityOS import State, Universe

class TestACNSolver(unittest.TestCase):
    def test_acn_convergence_parity(self):
        """Assert that decentralized ACN reaches the same equilibrium as centralized KKT."""
        # Setup a 5-node ring
        size = 5
        r = 5.0
        
        # Ground truth coordinates
        gt_coords = []
        for i in range(size):
            angle = 2.0 * math.pi * i / size
            gt_coords.append([r * math.cos(angle), r * math.sin(angle)])
            
        # 1. Run KKT baseline
        u_kkt = Universe(eta=0.08, alpha_dual=0.05)
        for i in range(size):
            node = u_kkt.create_state(name=f"node_{i}", dim=2)
            # Inject a small coordinate perturbation to force solving
            node.coords = [gt_coords[i][0] + 0.2, gt_coords[i][1] - 0.2]
        u_kkt.initialize()
        
        expected_dist = math.sqrt((gt_coords[0][0]-gt_coords[1][0])**2 + (gt_coords[0][1]-gt_coords[1][1])**2)
        
        def make_constraint(idx_a: int, idx_b: int, dist_val: float):
            return lambda G: math.sqrt((G[idx_a][0] - G[idx_b][0])**2 + (G[idx_a][1] - G[idx_b][1])**2) - dist_val
            
        for i in range(size):
            u_kkt.apply_constraint(f"tether_{i}", make_constraint(i, (i + 1) % size, expected_dist))
            
        # Run KKT for 50 steps
        for _ in range(50):
            u_kkt.step()
            
        kkt_final_coords = [list(n.coords) for n in u_kkt.states]
        
        # 2. Run ACN solver
        u_acn = Universe(eta=0.08, alpha_dual=0.05)
        u_acn.use_negotiation = True
        for i in range(size):
            node = u_acn.create_state(name=f"node_{i}", dim=2)
            node.coords = [gt_coords[i][0] + 0.2, gt_coords[i][1] - 0.2]
        u_acn.initialize()
        
        for i in range(size):
            u_acn.apply_constraint(f"tether_{i}", make_constraint(i, (i + 1) % size, expected_dist))
            
        # Run ACN for 50 steps
        for _ in range(50):
            u_acn.step()
            
        acn_final_coords = [list(n.coords) for n in u_acn.states]
        
        # Compare coordinate parity (should be very close, e.g. within 0.05)
        for i in range(size):
            for d in range(2):
                diff = abs(kkt_final_coords[i][d] - acn_final_coords[i][d])
                self.assertTrue(diff < 0.05, f"ACN coordinate mismatch at node {i} dim {d}: diff={diff:.4f}")
                
        # Assert that final constraints are satisfied
        violations = [abs(c_fn(u_acn.engine.G)) for c_fn in u_acn.engine.constraints.values()]
        self.assertTrue(max(violations) < 0.02, f"ACN failed to satisfy constraints. Max violation: {max(violations):.4f}")

    def test_acn_sparsity_and_silence(self):
        """Verify O(k) update sparsity and total computational silence when stable."""
        size = 10
        r = 5.0
        
        gt_coords = []
        for i in range(size):
            angle = 2.0 * math.pi * i / size
            gt_coords.append([r * math.cos(angle), r * math.sin(angle)])
            
        u_acn = Universe(eta=0.08, alpha_dual=0.05)
        u_acn.use_negotiation = True
        for i in range(size):
            node = u_acn.create_state(name=f"node_{i}", dim=2)
            node.coords = gt_coords[i]
        u_acn.initialize()
        
        expected_dist = math.sqrt((gt_coords[0][0]-gt_coords[1][0])**2 + (gt_coords[0][1]-gt_coords[1][1])**2)
        
        def make_constraint(idx_a: int, idx_b: int, dist_val: float):
            return lambda G: math.sqrt((G[idx_a][0] - G[idx_b][0])**2 + (G[idx_a][1] - G[idx_b][1])**2) - dist_val
            
        for i in range(size):
            u_acn.apply_constraint(f"tether_{i}", make_constraint(i, (i + 1) % size, expected_dist))
            
        # Let's initialize all nodes to asleep
        for i in range(size):
            u_acn.engine.node_active[i] = False
            u_acn.engine.node_sleep_ticks[i] = 5
            
        # 1. Verify complete silence: when all nodes are asleep and there is no surprise,
        # stepping the universe should execute ZERO updates.
        initial_updates = u_acn.engine.update_count
        u_acn.step()
        self.assertEqual(u_acn.engine.update_count, initial_updates, "Inactive, silent system computed updates!")
        
        # 2. Perturb only Node 0
        u_acn.state_map["node_0"].goal([2.0, 2.0])
        
        # Step once. Goal should wake up Node 0. Node 0's displacement should trigger violations
        # on tether_0 (linking node 0 and 1) and tether_9 (linking node 9 and 0).
        # This should wake up Node 1 and Node 9.
        # Nodes 3, 4, 5, 6, 7 should remain fully asleep!
        u_acn.step()
        
        # Check active states
        active_states = list(u_acn.engine.node_active)
        self.assertTrue(active_states[0], "Perturbed node 0 did not wake up!")
        self.assertTrue(active_states[1], "Neighbor node 1 did not wake up on cascade!")
        self.assertTrue(active_states[9], "Neighbor node 9 did not wake up on cascade!")
        
        # Verify that nodes further away remained asleep
        self.assertFalse(active_states[4], "Distant node 4 woke up unnecessarily!")
        self.assertFalse(active_states[5], "Distant node 5 woke up unnecessarily!")
        
        # 3. Settle: release goal force and let it settle back to sleep
        u_acn.state_map["node_0"].goal([0.0, 0.0])
        for _ in range(30):
            u_acn.step()
            
        # The system should settle, and nodes should go back to sleep (active count = 0)
        final_active_count = sum(1 for active in u_acn.engine.node_active if active)
        self.assertEqual(final_active_count, 0, f"System failed to settle back to sleep. Active nodes: {final_active_count}")

if __name__ == "__main__":
    unittest.main()
