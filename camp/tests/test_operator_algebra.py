"""
test_operator_algebra.py — Unit tests for the Operator Algebra.

Verifies mathematical correctness and confluence properties of the 12 primitive
cognitive operators defined in Section 3 of the Phase 0 Cognitive Specification.
"""

import unittest
import time
from RealityOS.kernel.cognitive_state import CognitiveState, Evidence, Constraint
from RealityOS.kernel.evolution import AnalyticEvolution
from RealityOS.kernel.cognitive_field import CognitiveField2D
from RealityOS.kernel.operator_algebra import OperatorAlgebra


class TestOperatorAlgebra(unittest.TestCase):
    def setUp(self):
        self.evolution_engine = AnalyticEvolution(eta=0.1, alpha=0.15)
        self.field = CognitiveField2D("test_risk_field", width=10, height=10, dx=1.0)

    def test_observe_and_integrate(self):
        s = CognitiveState(uid="test_ce", x=[1.0, 2.0], value=0.5)
        
        # 1. Observe new evidence
        evidence = Evidence(source_id="vision_sensor", data=[1.5, 2.5], confidence=0.9, timestamp=time.time())
        s = OperatorAlgebra.Observe(s, evidence)
        
        self.assertEqual(s.x, [1.5, 2.5])
        self.assertEqual(len(s.evidence), 1)

        # 2. Predict next state
        p, tau_p = OperatorAlgebra.Predict(s, self.evolution_engine)
        self.assertEqual(len(p), 2)
        
        # 3. Integrate prediction
        s = OperatorAlgebra.Integrate(s, p, tau_p)
        self.assertTrue("Integrate" in s.meta["causal_trace"][-1])

    def test_intent_and_diffusion(self):
        s = CognitiveState(uid="agent_ce", x=[2.0, 2.0], value=0.8)
        
        # 1. Diffuse risk from CE location
        s = OperatorAlgebra.Diffuse(s, self.field, strength=10.0)
        self.field.step(dt=0.05)
        
        # 2. Verify field has non-zero value at emitter position
        self.assertTrue(self.field.value_at(2.0, 2.0) > 0.0)
        
        # 3. Apply intent field gradient to CE
        s = OperatorAlgebra.ApplyIntent(s, self.field)
        self.assertEqual(len(s.g), 2)

    def test_crdt_merge(self):
        """Verify CRDT confluence properties of the Merge operator."""
        s1 = CognitiveState(uid="cup_1", type_tag="cup", x=[1.0, 5.0], value=0.4)
        s2 = CognitiveState(uid="cup_1", type_tag="cup", x=[2.0, 4.0], value=0.7)
        
        s1.tau = [1.0, 1.0]
        s2.tau = [1.5, 1.5]
        
        # Merge s1 and s2
        merged = OperatorAlgebra.Merge(s1, s2)
        
        # 1. Verify component-wise max on observable state coordinates x
        self.assertEqual(merged.x, [2.0, 5.0])
        
        # 2. Verify value convergence (max)
        self.assertEqual(merged.value, 0.7)
        
        # 3. Verify precision addition (Bayesian update approximation)
        self.assertEqual(merged.tau, [2.5, 2.5])

    def test_split_and_forget(self):
        s = CognitiveState(uid="toolbox", x=[1.0, 2.0, 3.0, 4.0], value=0.8)
        
        # 1. Split toolbox
        s1, s2 = OperatorAlgebra.Split(s)
        self.assertEqual(s1.uid, "toolbox_alpha")
        self.assertEqual(s2.uid, "toolbox_beta")
        self.assertEqual(s1.x, [1.0, 2.0])
        self.assertEqual(s2.x, [3.0, 4.0])
        self.assertEqual(s1.value, 0.4)
        
        # 2. Forget older details on s
        s = OperatorAlgebra.Forget(s, budget=0.2)
        self.assertTrue(s.tau[0] < 1.0)
        self.assertEqual(s.energy_budget, 1.0)

    def test_compress_invariants(self):
        """Verify Compressor extracts common coordinate bounds as a Constraint."""
        states = [
            CognitiveState(uid="obj_1", x=[1.0, 5.0]),
            CognitiveState(uid="obj_2", x=[1.1, 8.0]),
            CognitiveState(uid="obj_3", x=[0.9, 12.0])
        ]
        
        # Dimension 0 is rigid (variance is low), Dimension 1 has high variance
        rule = OperatorAlgebra.Compress(states)
        
        self.assertEqual(rule.dimension, 0)
        # Bounding limits should clamp around [0.9 - 0.1, 1.1 + 0.1] = [0.8, 1.2]
        self.assertAlmostEqual(rule.lower, 0.8)
        self.assertAlmostEqual(rule.upper, 1.2)

    def test_explain_and_schedule(self):
        s1 = CognitiveState(uid="ce_1", x=[0.0], value=0.2)
        s2 = CognitiveState(uid="ce_2", x=[0.0], value=1.0)
        
        s1.meta["surprise"] = 0.1
        s2.meta["surprise"] = 5.0 # high surprise
        
        # 1. Schedule based on priority
        queue = [s1, s2]
        scheduled = OperatorAlgebra.Schedule(queue, budget=1)
        
        # Highest value * surprise (ce_2) must be scheduled first
        self.assertEqual(len(scheduled), 1)
        self.assertEqual(scheduled[0].uid, "ce_2")
        
        # 2. Causal Explain verification
        trace = OperatorAlgebra.Explain(s1)
        self.assertTrue(isinstance(trace, list))


if __name__ == "__main__":
    unittest.main()
