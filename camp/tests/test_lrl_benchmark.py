"""
test_lrl_benchmark.py — Latent Relational Law (LRL) Benchmark.

Tests Hypothesis H3: The Constraint Compiler (Explain operator) can discover
an unknown pairwise distance invariant and reduce future surprise Action by >= 30%.
"""

import unittest
import math
import random
from RealityOS.kernel.relational_engine import RelationalEngine

class TestLRLBenchmark(unittest.TestCase):
    def test_latent_relational_law_discovery(self):
        """Validate discovery of hidden pairwise invariant and Action reduction."""
        random.seed(42)
        steps = 1000
        noise_std = 0.15
        rod_length = 3.0
        
        # 1. Generate ground truth trajectory of 2 coupled particles
        # Particle 0 rotates around the origin.
        # Particle 1 is coupled at a fixed distance (rod_length) and rotates relative to Particle 0.
        gt_trajectory = []
        for t in range(steps):
            w1 = 0.05 * t
            w2 = 0.12 * t
            p0 = [2.0 * math.sin(w1), 2.0 * math.cos(w1)]
            p1 = [p0[0] + rod_length * math.cos(w2), p0[1] + rod_length * math.sin(w2)]
            gt_trajectory.append([p0, p1])

        # 2. RUN CONDITION 1: Baseline Relational Engine (No constraints registered)
        # It just absorbs noisy observations.
        baseline_engine = RelationalEngine(size=2, eta=0.08)
        baseline_surprise_sum = 0.0
        
        for t in range(steps):
            p0_noisy = [gt_trajectory[t][0][0] + random.gauss(0, noise_std), gt_trajectory[t][0][1] + random.gauss(0, noise_std)]
            p1_noisy = [gt_trajectory[t][1][0] + random.gauss(0, noise_std), gt_trajectory[t][1][1] + random.gauss(0, noise_std)]
            
            # Predict step (baseline does zero-order hold prediction)
            p0_pred = list(baseline_engine.G[0])
            p1_pred = list(baseline_engine.G[1])
            
            # Compute surprise: squared prediction error
            surprise = (p0_noisy[0] - p0_pred[0])**2 + (p0_noisy[1] - p0_pred[1])**2 + \
                       (p1_noisy[0] - p1_pred[0])**2 + (p1_noisy[1] - p1_pred[1])**2
            baseline_surprise_sum += surprise
            
            # Update coordinate state directly with noisy observation
            baseline_engine.observe(0, p0_noisy)
            baseline_engine.observe(1, p1_noisy)

        # 3. RUN CONSTRAINT COMPILER (Explain) on a short initial history
        # We simulate the first 100 steps of noisy trajectory data to feed the compiler
        history_trajectory = []
        for t in range(100):
            p0_noisy = [gt_trajectory[t][0][0] + random.gauss(0, noise_std * 0.1), gt_trajectory[t][0][1] + random.gauss(0, noise_std * 0.1)]
            p1_noisy = [gt_trajectory[t][1][0] + random.gauss(0, noise_std * 0.1), gt_trajectory[t][1][1] + random.gauss(0, noise_std * 0.1)]
            history_trajectory.append([p0_noisy, p1_noisy])
            
        compiled_engine = RelationalEngine(size=2, eta=0.08, alpha_dual=0.1)
        # Discover invariant:
        discovered_rules = compiled_engine.explain(trajectory=history_trajectory, threshold=0.02)
        
        # Verify that distance_0_1 is discovered
        self.assertTrue(len(discovered_rules) > 0, "Constraint Compiler failed to discover any invariants.")
        rule_name, constraint_fn = discovered_rules[0]
        self.assertEqual(rule_name, "distance_0_1")
        
        # Register compiled constraint
        compiled_engine.perturb(rule_name, constraint_fn, initial_lambda=5.0)

        # 4. RUN CONDITION 2: Relational Engine with the Compiled Invariant Constraint
        compiled_surprise_sum = 0.0
        # Initialize compiled engine at starting point
        compiled_engine.observe(0, gt_trajectory[0][0])
        compiled_engine.observe(1, gt_trajectory[0][1])
        
        for t in range(steps):
            p0_noisy = [gt_trajectory[t][0][0] + random.gauss(0, noise_std), gt_trajectory[t][0][1] + random.gauss(0, noise_std)]
            p1_noisy = [gt_trajectory[t][1][0] + random.gauss(0, noise_std), gt_trajectory[t][1][1] + random.gauss(0, noise_std)]
            
            # Predict step
            p0_pred = list(compiled_engine.G[0])
            p1_pred = list(compiled_engine.G[1])
            
            surprise = (p0_noisy[0] - p0_pred[0])**2 + (p0_noisy[1] - p0_pred[1])**2 + \
                       (p1_noisy[0] - p1_pred[0])**2 + (p1_noisy[1] - p1_pred[1])**2
            compiled_surprise_sum += surprise
            
            # Observe and resolve constraints (KKT dual projection filters observation noise)
            compiled_engine.observe(0, p0_noisy)
            compiled_engine.observe(1, p1_noisy)
            compiled_engine.resolve(dt=0.1)

        # 5. Evaluate Action Reduction: delta_R = (compiled_surprise / baseline_surprise) - 1.0
        # We expect compiled_surprise_sum to be substantially lower because the constraint corrections
        # filter out the destructive coordinate noise.
        action_ratio = compiled_surprise_sum / baseline_surprise_sum
        delta_R = action_ratio - 1.0
        
        print(f"\n============================================================")
        print(f"       LATENT RELATIONAL LAW BENCHMARK (LRL) RESULTS")
        print(f"============================================================")
        print(f"Baseline Surprise Action:    {baseline_surprise_sum:.4f}")
        print(f"Compiled Surprise Action:    {compiled_surprise_sum:.4f}")
        print(f"Surprise Action Reduction:   {-delta_R * 100.0:.3f}% (Success threshold: >= 30.0%)")
        print(f"Discovered Relational Rule:  {rule_name}")
        print(f"Compiled Rule Target Distance: {math.sqrt((compiled_engine.G[0][0]-compiled_engine.G[1][0])**2 + (compiled_engine.G[0][1]-compiled_engine.G[1][1])**2):.4f}")
        print(f"============================================================")
        
        # Verify Action reduction success criteria (delta_R < -0.3)
        self.assertTrue(delta_R <= -0.3, f"Surprise Action reduction of {delta_R * 100.0:.3f}% was below 30% threshold.")

if __name__ == "__main__":
    unittest.main()
