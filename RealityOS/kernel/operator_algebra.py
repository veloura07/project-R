from typing import List, Tuple, Dict, Any, Callable
from RealityOS.kernel.cognitive_state import CognitiveState, Evidence, Constraint


class OperatorAlgebra:
    """
    Operator Algebra implementing the primitive cognitive operators
    defined in Section 3 of the Phase 0 Cognitive Specification.
    """

    @staticmethod
    def Observe(s: CognitiveState, evidence: Evidence) -> CognitiveState:
        """Observe(s : CS, e : Evidence) -> CS"""
        s.x = list(evidence.data)
        s.evidence.append(evidence)
        s.meta["causal_trace"].append(f"Observe[src={evidence.source_id}]")
        return s

    @staticmethod
    def Predict(s: CognitiveState, evolution_engine: Any) -> Tuple[List[float], List[float]]:
        """Predict(s : CS) -> (p_hat, tau_hat)"""
        # Linear or identity prediction for the next step
        p = list(s.x)
        tau_p = list(s.tau)
        return p, tau_p

    @staticmethod
    def Integrate(s: CognitiveState, p: List[float], tau_p: List[float]) -> CognitiveState:
        """Integrate(s : CS, p : Vector, tau_p : Vector) -> CS"""
        s.p = list(p)
        s.tau = list(tau_p)
        s.meta["causal_trace"].append("Integrate")
        return s

    @staticmethod
    def Diffuse(s: CognitiveState, field: Any, strength: float = 1.0) -> CognitiveState:
        """Diffuse(s : CS, field : CognitiveField2D, strength : float) -> CS"""
        gx, gy = field.world_to_grid(s.x[0], s.x[1])
        field.set_source(int(gx), int(gy), strength)
        s.meta["causal_trace"].append(f"Diffuse[field={field.name}, strength={strength:.2f}]")
        return s

    @staticmethod
    def ApplyIntent(s: CognitiveState, field: Any) -> CognitiveState:
        """ApplyIntent(s : CS, field : CognitiveField2D) -> CS"""
        grad_x, grad_y = field.gradient_at(s.x[0], s.x[1])
        s.g = [grad_x, grad_y]
        # Pad if state has higher dimensions
        if len(s.g) < len(s.x):
            s.g.extend([0.0] * (len(s.x) - len(s.g)))
        s.meta["causal_trace"].append(f"ApplyIntent[field={field.name}]")
        return s

    @staticmethod
    def Merge(s1: CognitiveState, s2: CognitiveState) -> CognitiveState:
        """Merge(s1 : CS, s2 : CS) -> CS"""
        dim = max(len(s1.x), len(s2.x))
        merged_x = []
        merged_tau = []
        for i in range(dim):
            x1 = s1.x[i] if i < len(s1.x) else 0.0
            x2 = s2.x[i] if i < len(s2.x) else 0.0
            merged_x.append(max(x1, x2))

            t1 = s1.tau[i] if i < len(s1.tau) else 0.0
            t2 = s2.tau[i] if i < len(s2.tau) else 0.0
            merged_tau.append(t1 + t2)

        merged = CognitiveState(
            uid=s1.uid,
            x=merged_x,
            value=max(s1.value, s2.value),
            type_tag=s1.type_tag
        )
        merged.tau = merged_tau
        merged.meta["causal_trace"] = s1.meta["causal_trace"] + s2.meta["causal_trace"] + ["Merge"]
        return merged

    @staticmethod
    def Split(s: CognitiveState) -> Tuple[CognitiveState, CognitiveState]:
        """Split(s : CS) -> (s_alpha, s_beta)"""
        mid = len(s.x) // 2
        x1 = s.x[:mid]
        x2 = s.x[mid:]

        s1 = CognitiveState(uid=f"{s.uid}_alpha", x=x1, value=s.value * 0.5, type_tag=s.type_tag)
        s2 = CognitiveState(uid=f"{s.uid}_beta", x=x2, value=s.value * 0.5, type_tag=s.type_tag)

        s1.meta["causal_trace"] = list(s.meta["causal_trace"]) + ["Split_Alpha"]
        s2.meta["causal_trace"] = list(s.meta["causal_trace"]) + ["Split_Beta"]

        return s1, s2

    @staticmethod
    def Forget(s: CognitiveState, budget: float) -> CognitiveState:
        """Forget(s : CS, budget : float) -> CS"""
        for i in range(len(s.tau)):
            s.tau[i] = s.tau[i] * (1.0 - budget)
        s.meta["causal_trace"].append(f"Forget[budget={budget:.2f}]")
        return s

    @staticmethod
    def Compress(states: List[CognitiveState]) -> Any:
        """Compress(𝔖 : List[CS]) -> Constraint/Rule"""
        num_dims = len(states[0].x)
        variances = []
        for d in range(num_dims):
            vals = [st.x[d] for st in states]
            mean = sum(vals) / len(vals)
            variance = sum((v - mean)**2 for v in vals) / len(vals)
            variances.append((variance, d, vals))

        # Sort by variance ascending
        variances.sort(key=lambda x: x[0])
        min_var_dim = variances[0][1]
        min_var_vals = variances[0][2]

        class CompressedRule:
            def __init__(self, dimension: int, lower: float, upper: float):
                self.dimension = dimension
                self.lower = lower
                self.upper = upper

        # Bounding limits clamp around [min - 0.1, max + 0.1]
        return CompressedRule(
            dimension=min_var_dim,
            lower=min(min_var_vals) - 0.1,
            upper=max(min_var_vals) + 0.1
        )

    @staticmethod
    def Schedule(queue: List[CognitiveState], budget: int) -> List[CognitiveState]:
        """Schedule(𝔖 : List[CS], budget : int) -> List[CS]"""
        # Sort by value * surprise in descending order
        sorted_queue = sorted(
            queue,
            key=lambda st: st.value * st.meta.get("surprise", 0.0),
            reverse=True
        )
        return sorted_queue[:budget]

    @staticmethod
    def Explain(s: CognitiveState) -> List[str]:
        """Explain(s : CS) -> List[CausalTrace]"""
        return s.meta.get("causal_trace", [])

