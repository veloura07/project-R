"""
test_aether_kernel.py — Verification of the Five Primitive Laws and 14 API Primitives.
"""

import unittest
import math
from RealityOS.kernel.aether_kernel import AetherUniverse

class TestAetherKernel(unittest.TestCase):
    def test_five_primitive_laws(self):
        """
        Verify the Five Primitive Laws sequentially in a simple 3-node system.
        """
        universe = AetherUniverse(size=3, dim=2, eta=0.08, alpha_dual=0.05)
        
        # --- LAW 1: Everything is an Event ---
        # --- LAW 2: Events create Relationships ---
        # 1. Ingest observations (Law 1 events)
        evt_obs_0 = universe.observe(0, [0.0, 0.0])
        evt_obs_1 = universe.observe(1, [2.0, 0.0])
        evt_obs_2 = universe.observe(2, [0.0, 1.5])
        
        self.assertEqual(len(universe.events), 3)
        self.assertEqual(evt_obs_0.event_type, "OBSERVATION")
        self.assertEqual(evt_obs_1.delta, [2.0, 0.0])
        
        # 2. Relate node 0 to node 1, and node 0 to node 2 (Law 2 edges)
        evt_rel_1 = universe.relate(0, 1)
        evt_rel_2 = universe.relate(0, 2)
        
        self.assertEqual(len(universe.events), 5)
        self.assertEqual(evt_rel_1.event_type, "RELATION")
        self.assertIn(1, universe.relations[0])
        self.assertIn(0, universe.relations[1])
        
        # --- LAW 3: Stable relationships become Constraints ---
        # Log a trajectory history where distance between Node 0 and Node 1 is stable at 2.0
        # and Node 0 and Node 2 is stable at 1.5.
        universe.trajectory_history = [
            [[0.0, 0.0], [2.0, 0.0], [0.0, 1.5]],
            [[0.05, -0.05], [2.05, -0.05], [0.05, 1.45]],
            [[-0.05, 0.05], [1.95, 0.05], [-0.05, 1.55]]
        ]
        
        discovered_events = universe.discover(threshold=0.01)
        self.assertEqual(len(discovered_events), 2)
        self.assertIn("dist_invariant_0_1", universe.constraints)
        self.assertIn("dist_invariant_0_2", universe.constraints)
        
        # --- LAW 4: Constraints bend State ---
        # Inject coordinate perturbation that violates the constraints
        universe.states[0].coords = [0.0, 0.0]
        universe.states[1].coords = [2.5, 0.0]  # Distance is 2.5 instead of 2.0
        
        # Stabilize: active constraint negotiation bends state back to equilibrium
        # Perform several steps of stabilize
        for _ in range(10):
            universe.stabilize(dt=0.1)
            
        # Verify coordinates bent to satisfy constraints
        final_G = universe.get_G()
        actual_dist = math.sqrt((final_G[0][0] - final_G[1][0])**2 + (final_G[0][1] - final_G[1][1])**2)
        self.assertTrue(abs(actual_dist - 2.0) < 0.15, f"Constraint did not bend state. Distance: {actual_dist:.4f}")
        
        # --- LAW 5: State creates new Events ---
        # Assert that coordinate updates generated TRANSITION events in the event log
        transition_events = [evt for evt in universe.events if evt.event_type == "TRANSITION"]
        self.assertTrue(len(transition_events) > 0, "No state transitions emitted events!")
        self.assertEqual(transition_events[0].event_type, "TRANSITION")

    def test_fourteen_api_primitives(self):
        """
        Verify the complete Unix-style 14 API primitives suite.
        """
        universe = AetherUniverse(size=3, dim=2, eta=0.08, alpha_dual=0.05)
        
        # 1. observe()
        universe.observe(0, [0.0, 0.0])
        universe.observe(1, [3.0, 0.0])
        
        # 2. relate()
        universe.relate(0, 1)
        
        # 3. constrain()
        # Rigid distance = 3.0
        def dist_viol(G):
            return math.sqrt((G[0][0]-G[1][0])**2 + (G[0][1]-G[1][1])**2) - 3.0
        universe.constrain("dist_3", dist_viol, "||G[0]-G[1]|| - 3.0 = 0")
        self.assertIn("dist_3", universe.constraints)
        
        # 4. stabilize()
        universe.stabilize()
        
        # 5. predict()
        # Setup velocities
        universe.states[0].velocity = [0.1, -0.1]
        universe.states[1].velocity = [-0.1, 0.1]
        preds = universe.predict(steps=3, dt=0.1)
        self.assertEqual(len(preds), 3)
        self.assertEqual(len(preds[0]), 3) # 3 nodes
        self.assertTrue(preds[0][0][0] > 0.0) # Node 0 X moved positive
        
        # 6. simulate()
        sim_traj = universe.simulate(steps=2, dt=0.1)
        self.assertEqual(len(sim_traj), 2)
        
        # 7. fork()
        forked = universe.fork()
        self.assertEqual(forked.size, universe.size)
        self.assertIn("dist_3", forked.constraints)
        
        # Verify isolation
        forked.states[0].coords = [99.0, 99.0]
        self.assertNotEqual(universe.states[0].coords, [99.0, 99.0])
        
        # 8. merge()
        merged = universe.merge(forked)
        self.assertEqual(merged.size, 6) # 3 + 3
        self.assertIn("dist_3", merged.constraints)
        self.assertIn("merged_dist_3", merged.constraints)
        
        # 9. rollback()
        universe.trajectory_history = [
            [[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]],
            [[5.0, 5.0], [6.0, 6.0], [7.0, 7.0]]
        ]
        universe.rollback(ticks=1)
        self.assertEqual(universe.states[0].coords, [5.0, 5.0])
        
        # 10. forget()
        initial_trust = universe.constraints["dist_3"].trust
        universe.forget(rate=0.2)
        self.assertTrue(universe.constraints["dist_3"].trust < initial_trust)
        
        # 11. compress()
        universe.trajectory_history = [
            [[5.0, 5.0], [6.0, 6.0], [7.0, 7.0]],
            [[5.05, 4.95], [6.0, 6.0], [7.0, 7.0]],
            [[4.95, 5.05], [6.0, 6.0], [7.0, 7.0]]
        ]
        bounds = universe.compress(threshold=0.01)
        self.assertTrue(len(bounds) > 0)
        self.assertEqual(bounds[0][0], 0) # node 0 compressed bounds
        
        # 12. discover()
        # (Tested in five laws, but check return here)
        discovered = universe.discover(threshold=0.01)
        self.assertEqual(len(discovered), 0) # Already discovered or no relations setup
        
        # 13. evolve()
        initial_energy = universe.constraints["dist_3"].energy
        # Artificially modify trust to be small to force energy decay
        universe.constraints["dist_3"].trust = 0.01
        universe.evolve()
        self.assertTrue(universe.constraints["dist_3"].energy < initial_energy)
        
        # 14. measure()
        metrics = universe.measure()
        self.assertIn("entropy", metrics)
        self.assertIn("potential_energy", metrics)
        self.assertIn("metabolism", metrics)

if __name__ == "__main__":
    unittest.main()
