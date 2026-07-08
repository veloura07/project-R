"""
test_r_identity.py — Benchmark R-Identity (RI) with KKT Primal-Dual Relational Engine vs RNN,
and numerical validation of representation theorems (RNN-CT, Bellman-CT).
"""

import unittest
import math
import random
from typing import List
from RealityOS.kernel.relational_engine import RelationalEngine

class SimpleRNNBaseline:
    """A baseline RNN that tries to maintain state representations without explicit constraints."""
    def __init__(self, size: int = 20, dim: int = 2, hidden_dim: int = 32):
        self.size = size
        self.dim = dim
        self.hidden_dim = hidden_dim
        
        self.wh = [[random.uniform(-0.1, 0.1) for _ in range(hidden_dim)] for _ in range(hidden_dim)]
        self.wx = [[random.uniform(-0.1, 0.1) for _ in range(hidden_dim)] for _ in range(dim)]
        self.wy = [[random.uniform(-0.1, 0.1) for _ in range(dim)] for _ in range(hidden_dim)]
        
        self.h = [[0.0 for _ in range(hidden_dim)] for _ in range(size)]
        self.states = [[0.0 for _ in range(dim)] for _ in range(size)]

    def step(self, inputs: List[List[float]], mask: List[bool], noise_level: float = 0.05):
        for i in range(self.size):
            x_in = inputs[i] if not mask[i] else [0.0] * self.dim
            
            new_h = [0.0] * self.hidden_dim
            for h_out in range(self.hidden_dim):
                val = 0.0
                for h_in in range(self.hidden_dim):
                    val += self.wh[h_out][h_in] * self.h[i][h_in]
                for x_in_idx in range(self.dim):
                    val += self.wx[h_out][x_in_idx] * x_in[x_in_idx]
                new_h[h_out] = math.tanh(val)
            self.h[i] = new_h
            
            pred = [0.0] * self.dim
            for d in range(self.dim):
                val = 0.0
                for h_in in range(self.hidden_dim):
                    val += self.wy[d][h_in] * self.h[i][h_in]
                pred[d] = val + random.gauss(0, noise_level)
            self.states[i] = pred

class TestRIdentity(unittest.TestCase):
    def test_r_identity_occlusion(self):
        """Validate R-Identity preservation under 10,000 steps of occlusion with KKT updates."""
        random.seed(42)
        size = 20
        steps = 10000
        noise_std = 0.02
        r_ideal = 5.0
        
        # 1. Initialize ground truth circle coordinates
        gt_coords = []
        for i in range(size):
            angle = 2.0 * math.pi * i / size
            gt_coords.append([r_ideal * math.cos(angle), r_ideal * math.sin(angle)])

        # 2. Setup Relational Engine with KKT dual learning rate
        engine = RelationalEngine(size=size, eta=0.08, alpha_dual=0.05)
        for i in range(size):
            init_pos = [gt_coords[i][0] + random.gauss(0, 0.01), gt_coords[i][1] + random.gauss(0, 0.01)]
            engine.observe(i, init_pos)

        # Ring adjacent distance constraints
        expected_dist = math.sqrt(
            (gt_coords[0][0] - gt_coords[1][0]) ** 2 +
            (gt_coords[0][1] - gt_coords[1][1]) ** 2
        )
        
        def make_constraint(idx: int):
            next_idx = (idx + 1) % size
            return lambda G: (math.sqrt((G[idx][0] - G[next_idx][0])**2 + (G[idx][1] - G[next_idx][1])**2) - expected_dist)

        for i in range(size):
            engine.perturb(f"ring_{i}", make_constraint(i), initial_lambda=1.0)

        # 3. Setup RNN Baseline
        rnn = SimpleRNNBaseline(size=size, dim=2)
        for i in range(size):
            rnn.states[i] = list(engine.G[i])

        # 4. Simulation loop (node 0 occluded)
        mask = [False] * size
        mask[0] = True
        
        pressure_log = []
        
        for step in range(steps):
            noisy_obs = []
            for i in range(size):
                noisy_obs.append([gt_coords[i][0] + random.gauss(0, noise_std), gt_coords[i][1] + random.gauss(0, noise_std)])
            
            # Observe unmasked nodes
            for i in range(size):
                if not mask[i]:
                    engine.observe(i, noisy_obs[i])
                    
            engine.resolve(dt=0.1)
            rnn.step(noisy_obs, mask, noise_level=noise_std)
            
            # Log ring 0 KKT multiplier value (pressure)
            pressure_log.append(engine.lambdas["ring_0"])

        # 5. Verify the Constraint Compiler (Explain Operator)
        invariants = engine.explain(threshold=0.01)
        self.assertTrue(len(invariants) > 0, "Explain compiler failed to discover the radial invariant.")
        self.assertEqual(invariants[0][0], "radial_invariant")
        
        # Verify compiled constraint evaluation
        compiled_fn = invariants[0][1]
        violation = compiled_fn(engine.G)
        self.assertTrue(abs(violation) < 0.1, f"Discovered radial invariant evaluated with high error: {violation:.4f}")

        # 6. Measure eigen-spectrum drift
        def compute_mean_radius(coords):
            cx = sum(c[0] for c in coords) / len(coords)
            cy = sum(c[1] for c in coords) / len(coords)
            radii = [math.sqrt((c[0] - cx)**2 + (c[1] - cy)**2) for c in coords]
            return sum(radii) / len(radii)

        re_final_radius = compute_mean_radius(engine.G)
        rnn_final_radius = compute_mean_radius(rnn.states)

        re_drift = abs(re_final_radius - r_ideal) / r_ideal
        rnn_drift = abs(rnn_final_radius - r_ideal) / r_ideal

        print(f"\n============================================================")
        print(f"       R-IDENTITY BENCHMARK RESULTS (10,000 STEPS - KKT)")
        print(f"============================================================")
        print(f"Relational Engine Radial Drift: {re_drift * 100.0:.3f}% (Success threshold: <= 5.000%)")
        print(f"Baseline RNN Radial Drift:      {rnn_drift * 100.0:.3f}%")
        print(f"Discovered Invariants Count:    {len(invariants)} ({invariants[0][0]})")
        print(f"Compiled Invariant Violation:   {violation:.4f}")
        print(f"Final KKT Pressure Ring 0:       {pressure_log[-1]:.4f}")
        print(f"============================================================")

        # Asserts
        self.assertTrue(re_drift <= 0.05, f"Relational Engine drift of {re_drift:.3f} exceeded 5% limit.")
        self.assertTrue(rnn_drift > 0.50, "Baseline RNN failed to show significant drift.")

    def test_rnn_representation_mapping(self):
        """Verify Theorem A: Embedding of a 3-unit RNN step into a CT Constraint model."""
        random.seed(42)
        h = [0.1, -0.2, 0.5]
        x = [0.8, -0.4]
        b = [0.1, 0.0, -0.1]
        
        W_hh = [[0.1, -0.2, 0.3], [0.4, 0.5, -0.1], [-0.3, 0.2, 0.6]]
        W_xh = [[0.5, 0.1], [-0.2, 0.3], [0.4, -0.5]]
        
        # Standard RNN calculation
        h_next_expected = [0.0] * 3
        for i in range(3):
            val = b[i]
            for j in range(3):
                val += W_hh[i][j] * h[j]
            for k in range(2):
                val += W_xh[i][k] * x[k]
            h_next_expected[i] = math.tanh(val)

        # Relational Engine (CT) representation
        # Node coordinates represent RNN state h
        engine = RelationalEngine(size=3, eta=0.1)
        for i in range(3):
            engine.observe(i, [h[i], 0.0]) # Dim 0 stores hidden activation
            
        def rnn_constraint(G):
            # C(G) = sum_i (G[i][0] - tanh(W*G_prev + U*x + b))^2
            total_err = 0.0
            for i in range(3):
                target = b[i]
                for j in range(3):
                    # We compute the target relative to the previous hidden state (h)
                    target += W_hh[i][j] * h[j]
                for k in range(2):
                    target += W_xh[i][k] * x[k]
                total_err += (G[i][0] - math.tanh(target)) ** 2
            return total_err
            
        engine.perturb("rnn_update", rnn_constraint, initial_lambda=1.0)
        
        # Resolve should move G[i][0] towards h_next_expected
        # Since we initialized G at h, resolve pulls G towards the tanh attractor
        for _ in range(50):
            engine.resolve(dt=0.1)
            
        for i in range(3):
            drift = abs(engine.G[i][0] - h_next_expected[i])
            # The coordinate should converge directly to the RNN target state
            self.assertTrue(drift < 1e-2, f"RNN-CT coordinate {i} drift ({drift:.4f}) exceeded convergence limit.")
        print(f" [Theorem A] RNN-CT Embedding Convergence Verified: Success.")

    def test_bellman_representation_mapping(self):
        """Verify Theorem C: Value iteration step as a Bellman-CT update."""
        random.seed(42)
        # 3-state system
        r = [1.0, 0.0, -1.0]
        gamma = 0.9
        P = [[0.7, 0.2, 0.1], [0.3, 0.5, 0.2], [0.0, 0.1, 0.9]]
        
        V = [0.0, 0.0, 0.0]
        # Standard Bellman expectation step
        V_next_expected = [0.0] * 3
        for i in range(3):
            pv_sum = 0.0
            for j in range(3):
                pv_sum += P[i][j] * V[j]
            V_next_expected[i] = r[i] + gamma * pv_sum

        # Relational Engine (CT) representation
        engine = RelationalEngine(size=3, eta=0.1)
        for i in range(3):
            engine.observe(i, [V[i], 0.0])
            
        def bellman_constraint(G):
            total_err = 0.0
            for i in range(3):
                pv_sum = 0.0
                for j in range(3):
                    pv_sum += P[i][j] * V[j] # evaluate w.r.t previous state
                target = r[i] + gamma * pv_sum
                total_err += (G[i][0] - target) ** 2
            return total_err

        engine.perturb("bellman_iter", bellman_constraint, initial_lambda=1.0)
        
        for _ in range(50):
            engine.resolve(dt=0.1)
            
        for i in range(3):
            drift = abs(engine.G[i][0] - V_next_expected[i])
            self.assertTrue(drift < 1e-2, f"Bellman-CT coordinate {i} drift ({drift:.4f}) exceeded convergence limit.")
        print(f" [Theorem C] Bellman-CT Embedding Convergence Verified: Success.")

if __name__ == "__main__":
    unittest.main()
