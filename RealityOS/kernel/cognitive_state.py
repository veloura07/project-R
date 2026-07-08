from typing import List, Dict, Any, Callable

class Evidence:
    """Trust provenance definitions for observations."""
    def __init__(self, source_id: str, data: List[float], confidence: float, timestamp: float):
        self.source_id = source_id
        self.data = data
        self.confidence = confidence
        self.timestamp = timestamp


class Constraint:
    """Represents a boundary constraint on the state space."""
    def __init__(self, name: str, violation_fn: Callable[[List[float]], float]):
        self.name = name
        self.violation_fn = violation_fn

    def evaluate(self, x: List[float]) -> float:
        return self.violation_fn(x)


class CognitiveState:
    """
    The Cognitive State (CS) representation of an entity or metric.
    """
    def __init__(
        self,
        uid: str,
        x: List[float],
        value: float = 0.5,
        type_tag: str = "unknown"
    ):
        self.uid = uid
        self.type_tag = type_tag
        
        # State variables
        self.x = list(x)
        self.xdot = [0.0] * len(x)
        
        # Predictor belief
        self.p = list(x)                      # One-step ahead prediction
        self.tau = [1.0] * len(x)             # Precision / Trust
        
        # Goals, Values & Budgets
        self.value = value                    # Utility V
        self.g = [0.0] * len(x)               # Intent field pull force
        self.energy_budget = 1.0              # Normalized energy budget [0, 1]
        self.energy_used = 0.0
        
        # Constraints and evidence local to this state
        self.constraints: List[Constraint] = []
        self.evidence: List[Evidence] = []
        
        # Meta-cognition
        self.meta: Dict[str, Any] = {
            "surprise": 0.0,
            "surprise_ema": 0.0,
            "confused": False,
            "stable": True,
            "causal_trace": []
        }
