"""
ace_engine.py — Adaptive Constraint Evolution (ACE) Engine.

Implements the scientific model-building loop for RealityOS.
Autonomously proposes candidate constraints, evaluates them against observations,
promotes statistically valid ones, and retires inactive or refuted constraints.
"""

import math
from typing import List, Dict, Tuple, Callable, Any, Optional

class ConstraintHypothesis:
    """
    Represents a candidate constraint being evaluated by the scientific loop.
    """
    def __init__(
        self,
        name: str,
        violation_fn: Callable[[List[List[float]]], float],
        symbolic_form: str,
        initial_status: str = "candidate"
    ):
        self.name = name
        self.violation_fn = violation_fn
        self.symbolic_form = symbolic_form
        self.status = initial_status  # "candidate" | "active" | "retired"
        
        # Scoring metrics
        self.history: List[float] = []
        self.score = 0.5
        self.ticks_seen = 0
        self.idle_ticks = 0  # Number of ticks with low Lagrange multiplier pressure

    def update_stats(self, G: List[List[float]]):
        """Evaluate the constraint violation and update statistical history."""
        self.ticks_seen += 1
        try:
            violation = self.violation_fn(G)
        except Exception:
            violation = 999.0  # High penalty on evaluation error
            
        self.history.append(abs(violation))
        if len(self.history) > 50:
            self.history.pop(0)

        # Calculate score: inversely proportional to violation mean and variance
        if not self.history:
            self.score = 0.0
            return

        mean_viol = sum(self.history) / len(self.history)
        var_viol = sum((v - mean_viol)**2 for v in self.history) / len(self.history)

        # Score is between 0 and 1
        self.score = 1.0 / (1.0 + mean_viol + 5.0 * var_viol)


class ACEEngine:
    """
    Manages the lifecycle of constraints in RealityOS.
    Matches templates to generate hypotheses, promotes them, and retires them.
    """
    def __init__(
        self,
        size: int,
        dim: int = 2,
        promotion_threshold: float = 0.8,
        refutation_threshold: float = 1.5,
        max_idle_ticks: int = 30,
        min_eval_ticks: int = 5
    ):
        self.size = size
        self.dim = dim
        self.promotion_threshold = promotion_threshold
        self.refutation_threshold = refutation_threshold
        self.max_idle_ticks = max_idle_ticks
        self.min_eval_ticks = min_eval_ticks

        self.hypotheses: Dict[str, ConstraintHypothesis] = {}
        self.retired_names: set = set()
        self.evolution_log: List[str] = []

    def log_event(self, event: str):
        """Append an event to the evolution log."""
        self.evolution_log.append(event)
        # Keep log size bounded
        if len(self.evolution_log) > 100:
            self.evolution_log.pop(0)

    def propose_candidates(self, trajectory: List[List[List[float]]]):
        """
        Scan trajectory history using structural templates to generate hypotheses.
        Trajectory shape: T (steps) x N (nodes) x dim
        """
        if not trajectory or len(trajectory) < 5:
            return

        T_len = len(trajectory)

        # 1. Template: Pairwise Distance Invariance
        # Check all pairs of nodes (i, j) for constant distance over the trajectory.
        for i in range(self.size):
            for j in range(i + 1, self.size):
                name = f"distance_{i}_{j}"
                if name in self.hypotheses or name in self.retired_names:
                    continue

                dists = []
                for t in range(T_len):
                    g_t = trajectory[t]
                    if i < len(g_t) and j < len(g_t):
                        d = math.sqrt(sum((g_t[i][d] - g_t[j][d])**2 for d in range(self.dim)))
                        dists.append(d)
                
                if not dists:
                    continue

                mean_d = sum(dists) / len(dists)
                var_d = sum((d - mean_d)**2 for d in dists) / len(dists)

                # If variance is low, propose as candidate
                if var_d < 0.05:
                    # Capture indices and target distance via local closures
                    def make_distance_constraint(idx_a=i, idx_b=j, target_d=mean_d):
                        return lambda G: math.sqrt(sum((G[idx_a][d] - G[idx_b][d])**2 for d in range(self.dim))) - target_d

                    self.hypotheses[name] = ConstraintHypothesis(
                        name=name,
                        violation_fn=make_distance_constraint(),
                        symbolic_form=f"||G[{i}] - G[{j}]|| - {mean_d:.3f} = 0"
                    )
                    self.log_event(f"Hypothesized candidate: {name} (distance invariant = {mean_d:.3f})")

        # 2. Template: Radial Invariance
        # Check if nodes maintain constant distance from origin
        for i in range(self.size):
            name = f"radial_{i}"
            if name in self.hypotheses or name in self.retired_names:
                continue

            radii = []
            for t in range(T_len):
                g_t = trajectory[t]
                if i < len(g_t):
                    r = math.sqrt(sum(g_t[i][d]**2 for d in range(self.dim)))
                    radii.append(r)

            if not radii:
                continue

            mean_r = sum(radii) / len(radii)
            var_r = sum((r - mean_r)**2 for r in radii) / len(radii)

            if var_r < 0.05:
                def make_radial_constraint(idx=i, target_r=mean_r):
                    return lambda G: math.sqrt(sum(G[idx][d]**2 for d in range(self.dim))) - target_r

                self.hypotheses[name] = ConstraintHypothesis(
                    name=name,
                    violation_fn=make_radial_constraint(),
                    symbolic_form=f"||G[{i}]|| - {mean_r:.3f} = 0"
                )
                self.log_event(f"Hypothesized candidate: {name} (radial invariant = {mean_r:.3f})")

        # 3. Template: Coordinate Lock (static in one coordinate dimension)
        for i in range(self.size):
            for d in range(self.dim):
                name = f"coord_lock_{i}_{d}"
                if name in self.hypotheses or name in self.retired_names:
                    continue

                vals = [trajectory[t][i][d] for t in range(T_len) if i < len(trajectory[t])]
                if not vals:
                    continue

                mean_v = sum(vals) / len(vals)
                var_v = sum((v - mean_v)**2 for v in vals) / len(vals)

                if var_v < 0.01:
                    def make_coord_constraint(idx=i, dim_idx=d, target_v=mean_v):
                        return lambda G: G[idx][dim_idx] - target_v

                    self.hypotheses[name] = ConstraintHypothesis(
                        name=name,
                        violation_fn=make_coord_constraint(),
                        symbolic_form=f"G[{i}][{d}] - {mean_v:.3f} = 0"
                    )
                    self.log_event(f"Hypothesized candidate: {name} (coordinate {d} lock = {mean_v:.3f})")

    def evolve(self, relational_engine: Any, current_trajectory: List[List[List[float]]] = None):
        """
        Step the Adaptive Constraint Evolution cycle:
        1. Propose candidates from trajectory.
        2. Evaluate candidates against current state G.
        3. Promote valid ones to active constraints.
        4. Retire violated or redundant ones.
        """
        # 1. Propose candidates if trajectory history is provided
        if current_trajectory:
            self.propose_candidates(current_trajectory)

        G = relational_engine.G

        # 2. Evaluate all candidates and active hypotheses
        for h in list(self.hypotheses.values()):
            if h.status != "retired":
                h.update_stats(G)

        # 3. Promote candidates that exceed threshold
        for name, h in list(self.hypotheses.items()):
            if h.status == "candidate":
                if h.score >= self.promotion_threshold and h.ticks_seen >= self.min_eval_ticks:
                    # Consistency check: verify this doesn't conflict with existing active constraints
                    if self._is_consistent(name, relational_engine):
                        h.status = "active"
                        relational_engine.perturb(h.name, h.violation_fn, initial_lambda=1.0)
                        self.log_event(f"PROMOTED: {name} to ACTIVE (score={h.score:.3f})")
                    else:
                        h.status = "retired"
                        self.log_event(f"BLOCKED: {name} failed consistency check (conflicting constraint)")

        # 4. Monitor and retire active constraints
        for name, h in list(self.hypotheses.items()):
            if h.status == "active":
                # Check for refutation: current violation exceeds threshold
                try:
                    current_viol = abs(h.violation_fn(G))
                except Exception:
                    current_viol = 999.0

                # Check for redundancy/idle behavior: Lagrange pressure remains near-zero
                pressure = relational_engine.lambdas.get(name, 0.0)
                
                # Check if refuted by data
                if current_viol > self.refutation_threshold:
                    self._retire_constraint(name, h, relational_engine, f"REFUTED (violation={current_viol:.3f} > limit)")
                    continue

                # Track consecutive ticks with low pressure
                if pressure < 0.05:
                    h.idle_ticks += 1
                else:
                    h.idle_ticks = 0

                if h.idle_ticks >= self.max_idle_ticks:
                    self._retire_constraint(name, h, relational_engine, f"RETIRED (idle pressure {pressure:.3f} for {h.idle_ticks} ticks)")

    def _is_consistent(self, name: str, relational_engine: Any) -> bool:
        """Verify that a candidate constraint does not conflict with active constraints."""
        active_names = [h.name for h in self.hypotheses.values() if h.status == "active"]
        
        parts = name.split('_')
        if len(parts) >= 3:
            prefix = parts[0]
            if prefix == "distance":
                node_a, node_b = parts[1], parts[2]
                for active in active_names:
                    aparts = active.split('_')
                    if len(aparts) >= 3 and aparts[0] == "distance":
                        if (aparts[1] == node_a and aparts[2] == node_b) or (aparts[1] == node_b and aparts[2] == node_a):
                            return False
            elif prefix == "radial":
                node = parts[1]
                for active in active_names:
                    aparts = active.split('_')
                    if len(aparts) >= 2 and aparts[0] == "radial" and aparts[1] == node:
                        return False
            elif prefix == "coord":
                node, dim = parts[2], parts[3]
                for active in active_names:
                    aparts = active.split('_')
                    if len(aparts) >= 4 and aparts[0] == "coord" and aparts[2] == node and aparts[3] == dim:
                        return False
        return True

    def _retire_constraint(self, name: str, h: ConstraintHypothesis, relational_engine: Any, reason: str):
        """Helper to safely retire a constraint from the engine."""
        h.status = "retired"
        self.retired_names.add(name)
        
        # Remove from relational engine
        if name in relational_engine.constraints:
            relational_engine.constraints.pop(name)
        if name in relational_engine.lambdas:
            relational_engine.lambdas.pop(name)

        self.log_event(f"RETIRED: {name} — {reason}")

    def get_summary(self) -> Dict[str, Any]:
        """Return snapshots of candidates, active, and retired rules."""
        return {
            "candidates": [
                {"name": h.name, "form": h.symbolic_form, "score": h.score}
                for h in self.hypotheses.values() if h.status == "candidate"
            ],
            "active": [
                {"name": h.name, "form": h.symbolic_form, "score": h.score, "ticks": h.ticks_seen}
                for h in self.hypotheses.values() if h.status == "active"
            ],
            "retired": [
                {"name": h.name, "form": h.symbolic_form}
                for h in self.hypotheses.values() if h.status == "retired"
            ]
        }
