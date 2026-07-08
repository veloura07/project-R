"""
adaptive_interaction.py — The Adaptive Interaction (AIx) primitive for Project S.

Implements the fundamental interaction-coupling primitive between states.
Rather than standalone entities, the interaction is the atomic unit of
computational intelligence, conserving Adaptive Capacity (C).
"""

import uuid
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Optional


@dataclass
class CausalEvidence:
    source_id: str
    data: Any
    confidence: float
    timestamp: float


class AdaptiveInteraction:
    """
    The fundamental primitive of the Physics of Adaptive Systems: AIx.
    Represents the coupling between two states z_A and z_B.
    """

    def __init__(
        self,
        state_a_id: str,
        state_b_id: str,
        dim: int = 4,
        uid: Optional[str] = None,
        capacity: float = 1.0,  # Adaptive Capacity (C) allocated to this interaction
    ):
        self.uid = uid or str(uuid.uuid4())[:12]
        self.state_a_id = state_a_id
        self.state_b_id = state_b_id
        self.dim = dim

        # Conserved capacity parameter (thermodynamic bound)
        self.capacity = capacity

        # Coordinates for connected state spaces
        self.z_a = [0.0] * dim
        self.z_b = [0.0] * dim

        # Dynamics
        self.force = [0.0] * dim       # F_AB driving vector
        self.precision = [1.0] * dim   # tau_AB (precision/trust of the link)
        self.velocity_a = [0.0] * dim  # Rate of change of z_a
        self.velocity_b = [0.0] * dim  # Rate of change of z_b

        # Intrinsic Local Time parameters
        self.local_time = 0.0
        self.dt = 0.1                  # Local intrinsic time-step (adaptive)
        self.decay_rate = 0.05
        self.horizon = 1.0

        # Constraints local to this interaction
        self.constraints: List[Callable[[List[float]], float]] = []
        self.evidence: List[CausalEvidence] = []
        
        # Meta-cognition state
        self.meta: Dict[str, Any] = {
            "surprise": 0.0,
            "surprise_ema": 0.0,
            "stable": True,
            "causal_trace": []
        }

    def record_evidence(self, obs_a: List[float], obs_b: List[float], confidence: float, source: str):
        """Append raw observation evidence, conserving it monotonically."""
        self.evidence.append(
            CausalEvidence(
                source_id=source,
                data=(list(obs_a), list(obs_b)),
                confidence=confidence,
                timestamp=time.time()
            )
        )
        self.meta["causal_trace"].append(f"Observe[src={source}, conf={confidence:.2f}]")

    def update_precision(self, surprise: float):
        """
        Bayesian update of local precision tau based on surprise.
        High surprise decays precision; low surprise restores it.
        This is bounded by the allocated Adaptive Capacity (C).
        """
        for i in range(self.dim):
            if surprise > 1.5:
                # Decouple / decay trust
                decay = 0.1 * (1.0 / self.capacity)
                self.precision[i] = max(0.05, self.precision[i] * (1.0 - decay))
            else:
                # Build trust, capped by capacity
                growth = 0.05 * self.capacity
                self.precision[i] = min(5.0 * self.capacity, self.precision[i] * (1.0 + growth))
