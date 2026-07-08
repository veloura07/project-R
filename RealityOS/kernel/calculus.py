"""
calculus.py — The 5 universal operators of the Intelligence Calculus.

Implements Section 2.3 of the Phase 0 Cognitive Specification.
Every cognitive operation is a composition of these five:
    1. Observe
    2. Predict
    3. Transform
    4. Constrain
    5. Propagate
"""

import time
from typing import List, Tuple, Callable, Set, Dict, Any
from RealityOS.kernel.adaptive_interaction import AdaptiveInteraction, CausalEvidence
from RealityOS.kernel.evolution import DecentralizedEvolution


class Calculus:
    """
    The Intelligence Calculus operators.
    These are pure static methods that transform AdaptiveInteraction (AIx) states.
    """

    @staticmethod
    def Observe(
        ix: AdaptiveInteraction,
        obs_a: List[float],
        obs_b: List[float],
        confidence: float = 1.0,
        source: str = "environment"
    ) -> AdaptiveInteraction:
        """
        Observe(e : CEv, obs : Evidence) -> CEv
        Integrates raw observation evidence and logs causal provenance.
        """
        ix.z_a = list(obs_a)
        ix.z_b = list(obs_b)
        ix.record_evidence(obs_a, obs_b, confidence, source)
        return ix

    @staticmethod
    def Predict(
        ix: AdaptiveInteraction,
        predictor: Callable[[List[float]], List[float]]
    ) -> Tuple[List[float], List[float]]:
        """
        Predict(e : CEv) -> (z_hat, tau_hat)
        Evaluates local forward models to generate predictions and precisions.
        """
        z_hat = predictor(ix.z_a)
        # Precision acts as tau_hat
        return z_hat, list(ix.precision)

    @staticmethod
    def Transform(ix: AdaptiveInteraction, force: List[float]) -> AdaptiveInteraction:
        """
        Transform(e : CEv, Δz : Vector) -> CEv
        Applies a driving/control vector (intent force) to the interaction.
        """
        if len(force) == ix.dim:
            ix.force = list(force)
        ix.meta["causal_trace"].append(f"Transform[force_magnitude={sum(f**2 for f in force)**0.5:.2f}]")
        return ix

    @staticmethod
    def Constrain(ix: AdaptiveInteraction, constraint_fn: Callable[[List[float]], float]) -> AdaptiveInteraction:
        """
        Constrain(e : CEv, C : Callable) -> CEv
        Appends a local boundary or policy constraint onto the variational landscape.
        """
        ix.constraints.append(constraint_fn)
        ix.meta["causal_trace"].append("Constrain[registered_constraint]")
        return ix

    @staticmethod
    def Propagate(
        interactions: List[AdaptiveInteraction],
        evolution_engine: DecentralizedEvolution,
        threshold: float = 0.02
    ) -> List[Dict[str, Any]]:
        """
        Propagate(𝔈 : Set[CEv]) -> Set[CEv]
        Runs a decentralized evolution step only for interactions whose local
        surprise exceeds the active pressure threshold theta.
        This enforces O(k) sparse updates.
        """
        telemetries = []
        for ix in interactions:
            surprise = evolution_engine.compute_local_surprise(ix)
            if surprise > threshold:
                # Surprise triggers active Evolve step
                telemetry = evolution_engine.step(ix)
                telemetries.append(telemetry)
            else:
                # Sub-threshold: dynamic time-stepping stretches to conserve energy
                ix.dt = min(1.0, ix.dt * 1.05)
        return telemetries
