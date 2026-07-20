"""
test_ace_engine.py — Unit tests verifying the Adaptive Constraint Evolution (ACE) Engine.
"""

import unittest
import math
import random
from RealityOS.kernel.relational_engine import RelationalEngine
from RealityOS.kernel.ace_engine import ACEEngine

class TestACEEngine(unittest.TestCase):
    def test_hypothesis_generation(self):
        """Verify that the engine proposes the correct distance constraint from a clean trajectory."""
        size = 2
        steps = 10
        rod_length = 3.0
        
        # 1. Generate clean rotating trajectory of 2 coupled particles
        trajectory = []
        for t in range(steps):
            angle = 0.1 * t
            p0 = [0.0, 0.0]
            p1 = [rod_length * math.cos(angle), rod_length * math.sin(angle)]
            trajectory.append([p0, p1])
            
        engine = RelationalEngine(size=size, eta=0.05)
        # Manually trigger candidate proposal
        engine.ace.propose_candidates(trajectory)
        
        summary = engine.ace.get_summary()
        candidates = summary["candidates"]
        
        # We expect a distance_0_1 constraint to be proposed
        self.assertTrue(len(candidates) > 0, "No candidates were proposed.")
        self.assertEqual(candidates[0]["name"], "distance_0_1")
        self.assertIn("||G[0] - G[1]||", candidates[0]["form"])

    def test_constraint_promotion(self):
        """Verify that a candidate constraint is promoted to active after consistent evidence."""
        random.seed(42)
        size = 2
        steps = 15
        noise_std = 0.02
        rod_length = 3.0
        
        engine = RelationalEngine(size=size, eta=0.08, alpha_dual=0.1)
        # We set min_eval_ticks small so promotion happens quickly
        engine.ace.min_eval_ticks = 3
        engine.ace.promotion_threshold = 0.7
        
        # Initial positions
        engine.observe(0, [0.0, 0.0])
        engine.observe(1, [3.0, 0.0])
        
        trajectory_history = []
        
        # Feed the engine with observations over several ticks
        for t in range(steps):
            # Rotational trajectory with noise
            angle = 0.15 * t
            p0 = [random.gauss(0, noise_std), random.gauss(0, noise_std)]
            p1 = [p0[0] + rod_length * math.cos(angle) + random.gauss(0, noise_std),
                  p0[1] + rod_length * math.sin(angle) + random.gauss(0, noise_std)]
            
            engine.observe(0, p0)
            engine.observe(1, p1)
            
            # This automatically appends G to history and steps ACE
            engine.resolve(dt=0.1)
            
        summary = engine.ace.get_summary()
        active = summary["active"]
        
        # Verify that distance_0_1 is now active
        self.assertTrue(len(active) > 0, "No constraints were promoted to active.")
        active_names = [a["name"] for a in active]
        self.assertIn("distance_0_1", active_names)
        self.assertIn("distance_0_1", engine.constraints)

    def test_constraint_refutation_and_retirement(self):
        """Verify that an active constraint is retired when it is severely violated."""
        random.seed(42)
        size = 2
        steps_before_break = 10
        steps_after_break = 5
        rod_length = 3.0
        
        engine = RelationalEngine(size=size, eta=0.08, alpha_dual=0.1)
        engine.ace.min_eval_ticks = 2
        engine.ace.promotion_threshold = 0.7
        engine.ace.refutation_threshold = 1.0  # Retire if violation exceeds 1.0
        
        # Step 1: Normal rigid connection (promotes the constraint)
        for t in range(steps_before_break):
            angle = 0.2 * t
            p0 = [0.0, 0.0]
            p1 = [rod_length * math.cos(angle), rod_length * math.sin(angle)]
            engine.observe(0, p0)
            engine.observe(1, p1)
            engine.resolve(dt=0.1)
            
        # Verify it was promoted
        self.assertEqual(engine.ace.hypotheses["distance_0_1"].status, "active")
        self.assertIn("distance_0_1", engine.constraints)
        
        # Step 2: The rod breaks! Particle 1 flies away, violating the constraint
        for t in range(steps_after_break):
            p0 = [0.0, 0.0]
            p1 = [15.0, 15.0]  # True distance is ~21.2, massive violation of 3.0 constraint
            engine.observe(0, p0)
            engine.observe(1, p1)
            engine.resolve(dt=0.1)
            
        # Verify that the constraint is retired and removed
        self.assertEqual(engine.ace.hypotheses["distance_0_1"].status, "retired")
        self.assertNotIn("distance_0_1", engine.constraints)
        self.assertNotIn("distance_0_1", engine.lambdas)
        self.assertIn("distance_0_1", engine.ace.retired_names)
        
        summary = engine.ace.get_summary()
        retired_names = [r["name"] for r in summary["retired"]]
        self.assertIn("distance_0_1", retired_names)
        
        print("\n[ACE Evolution test] Successfully retired refuted distance_0_1 constraint after structural break.")

if __name__ == "__main__":
    unittest.main()
