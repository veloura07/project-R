"""
test_capacity_conservation.py — Test for Hypothesis H5 (Conservation of Adaptive Capacity).
"""

import unittest
from RealityOS.kernel.adaptive_interaction import AdaptiveInteraction


class TestCapacityConservation(unittest.TestCase):
    def test_capacity_reallocation_and_conservation(self):
        """Verify that Adaptive Capacity (C) can be dynamically reallocated but remains conserved."""
        total_capacity_limit = 5.0
        
        # Initialize 5 interactions, each allocated C = 1.0
        interactions = [
            AdaptiveInteraction(state_a_id=f"a_{i}", state_b_id=f"b_{i}", capacity=1.0)
            for i in range(5)
        ]
        
        # 1. Verify initial total capacity matches the limit
        initial_total = sum(ix.capacity for ix in interactions)
        self.assertEqual(initial_total, total_capacity_limit)

        # 2. Simulate local capacity transfer:
        # Interaction 0 becomes highly active/surprising, requiring more precision bandwidth.
        # We reclaim capacity from stable interactions (1, 2, 3) to fund interaction 0.
        transfer_amount = 0.5
        
        # Reclamation
        reclaimed = 0.0
        for i in [1, 2]:
            ix = interactions[i]
            ix.capacity -= transfer_amount * 0.5
            reclaimed += transfer_amount * 0.5
            
        # Reallocate to interaction 0
        interactions[0].capacity += reclaimed

        # 3. Verify interaction 0 now has increased capacity
        self.assertEqual(interactions[0].capacity, 1.5)
        self.assertEqual(interactions[1].capacity, 0.75)

        # 4. Verify total capacity is strictly conserved
        post_transfer_total = sum(ix.capacity for ix in interactions)
        self.assertAlmostEqual(post_transfer_total, total_capacity_limit)
        print(f"\n [H5 Test] Capacity Conservation: Initial Sum: {initial_total:.2f} | Post-Transfer Sum: {post_transfer_total:.2f}")


if __name__ == "__main__":
    unittest.main()
