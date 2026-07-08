"""
evolution.py — Decentralized Euler-Lagrange Dynamics for Project S.

Solves the continuous-time gradient descent evolution of Adaptive Interactions (AIx).
Updates connected states to minimize local free-energy J(x).
"""

import math
from typing import List, Callable, Dict, Any
from RealityOS.kernel.adaptive_interaction import AdaptiveInteraction


class DecentralizedEvolution:
    """
    Decentralized evolution engine.
    Optimizes local interaction configurations independently using gradient descent.
    """

    def __init__(
        self,
        lambda_c: float = 10.0,      # Constraint multiplier
        lambda_coord: float = 1.0,   # Coordination/force multiplier
        eta_base: float = 0.15,      # Base learning rate / temperature
    ):
        self.lambda_c = lambda_c
        self.lambda_coord = lambda_coord
        self.eta_base = eta_base

    def compute_local_surprise(self, ix: AdaptiveInteraction) -> float:
        """
        Compute local prediction error scaled by precision:
        surprise = sum_i tau_i * (z_a[i] - z_b[i])^2
        """
        surprise = 0.0
        for i in range(ix.dim):
            surprise += ix.precision[i] * (ix.z_a[i] - ix.z_b[i]) ** 2
        return surprise

    def compute_constraint_gradient(
        self,
        z: List[float],
        constraints: List[Callable[[List[float]], float]],
        dim: int
    ) -> List[float]:
        """Compute numerical gradient of constraint violations."""
        grad = [0.0] * dim
        eps = 1e-5

        for c in constraints:
            base_violation = c(z)
            if base_violation == 0.0:
                continue

            for i in range(dim):
                z_perturbed = list(z)
                z_perturbed[i] += eps
                perturbed_violation = c(z_perturbed)
                # Central difference
                grad[i] += (perturbed_violation - base_violation) / eps

        return grad

    def step(self, ix: AdaptiveInteraction) -> Dict[str, Any]:
        """
        Evolve a single interaction coupling step:
        1. Compute surprise.
        2. Calculate gradient updates.
        3. Step connected coordinates via Euler-Lagrange gradient flow.
        4. Adjust local dynamic time-step dt.
        """
        # 1. Compute Surprise
        surprise = self.compute_local_surprise(ix)
        ix.meta["surprise"] = surprise
        
        # Surprise EMA tracking
        ema = ix.meta.get("surprise_ema", 0.0)
        ix.meta["surprise_ema"] = ema * 0.85 + surprise * 0.15

        # 2. Adjust local dynamic time-step dt
        if surprise > 1.5:
            # Shrink time-step for fine-grained resolution under surprise
            ix.dt = max(0.01, ix.dt * 0.8)
        else:
            # Expand time-step to conserve computational energy
            ix.dt = min(1.0, ix.dt * 1.05)

        # 3. Calculate gradients of J
        # prediction gradient: tau * (z_a - z_b)
        grad_pred_a = [ix.precision[i] * (ix.z_a[i] - ix.z_b[i]) for i in range(ix.dim)]
        grad_pred_b = [ix.precision[i] * (ix.z_b[i] - ix.z_a[i]) for i in range(ix.dim)]

        # constraint gradient
        grad_constr_a = self.compute_constraint_gradient(ix.z_a, ix.constraints, ix.dim)

        # cognitive temperature scales with remaining capacity
        eta = self.eta_base * ix.capacity

        # 4. Evolve states: z = z - dt * eta * grad_J
        for i in range(ix.dim):
            # Euler-Lagrange dynamics for A
            force_term = self.lambda_coord * ix.force[i]
            z_dot_a = grad_pred_a[i] + self.lambda_c * grad_constr_a[i] + force_term
            ix.z_a[i] -= ix.dt * eta * z_dot_a
            
            # Euler-Lagrange dynamics for B (relaxation pull)
            z_dot_b = grad_pred_b[i]
            ix.z_b[i] -= ix.dt * eta * z_dot_b

            # Estimate local velocity
            ix.velocity_a[i] = -z_dot_a
            ix.velocity_b[i] = -z_dot_b

        # 5. Bayesian precision update
        ix.update_precision(surprise)
        ix.local_time += ix.dt
        ix.meta["causal_trace"].append(f"Evolve[dt={ix.dt:.3f}, surprise={surprise:.4f}]")

        return {
            "uid": ix.uid,
            "surprise": surprise,
            "dt": ix.dt,
            "precision": list(ix.precision),
            "stable": ix.meta["surprise_ema"] < 0.5
        }


class AnalyticEvolution:
    """
    Analytic evolution engine.
    Solves the continuous-time gradient descent evolution of CognitiveStates.
    """

    def __init__(
        self,
        eta: float = 0.1,
        alpha: float = 0.15,
        lambda_c: float = 20.0,
        lambda_g: float = 5.0,
    ):
        self.eta = eta
        self.alpha = alpha
        self.lambda_c = lambda_c
        self.lambda_g = lambda_g

    def step(self, s: Any, x: List[float]) -> Dict[str, Any]:
        """
        Evolve a single cognitive state step:
        1. Compute surprise.
        2. Calculate gradients.
        3. Step state coordinates via Euler integration.
        4. Adjust precision / trust based on surprise.
        """
        dim = len(s.x)
        
        # 1. Compute surprise (weighted prediction error)
        surprise = 0.0
        for i in range(dim):
            surprise += s.tau[i] * (s.x[i] - s.p[i]) ** 2
        s.meta["surprise"] = surprise
        
        # Surprise EMA tracking
        ema = s.meta.get("surprise_ema", 0.0)
        s.meta["surprise_ema"] = ema * 0.85 + surprise * 0.15

        # 2. Compute gradients of J
        # prediction gradient: tau * (x - p)
        grad_pred = [s.tau[i] * (s.x[i] - s.p[i]) for i in range(dim)]

        # constraint gradient (numerical approximation)
        grad_constr = [0.0] * dim
        eps = 1e-5
        for c in s.constraints:
            evaluate_fn = c.evaluate if hasattr(c, "evaluate") else c
            base_violation = evaluate_fn(s.x)
            if base_violation == 0.0:
                continue

            for i in range(dim):
                x_perturbed = list(s.x)
                x_perturbed[i] += eps
                perturbed_violation = evaluate_fn(x_perturbed)
                grad_constr[i] += (perturbed_violation - base_violation) / eps

        # Goal gradient: -g (pull toward attractor)
        grad_goal = [-s.g[i] for i in range(dim)]

        # 3. Integrate step (Euler step)
        dt = 0.05
        eta_eff = self.eta * s.energy_budget
        
        proposed_x = []
        for i in range(dim):
            z_dot = grad_pred[i] + self.lambda_c * grad_constr[i] + self.lambda_g * grad_goal[i]
            proposed_x.append(s.x[i] - dt * eta_eff * z_dot)
            s.xdot[i] = -z_dot

        # Apply update
        s.x = proposed_x

        # Deduct energy budget
        step_size = math.sqrt(sum(s.xdot[i]**2 for i in range(dim)))
        energy_cost = step_size * 0.02 + 0.005
        s.energy_budget = max(0.0, s.energy_budget - energy_cost)
        s.energy_used += energy_cost

        # 4. Bayesian trust (precision) update
        for i in range(dim):
            new_tau = s.tau[i] * (1.0 - self.alpha * surprise) + self.alpha
            s.tau[i] = max(0.1, min(5.0, new_tau))

        s.meta["causal_trace"].append(f"Evolve[surprise={surprise:.4f}, energy={s.energy_budget:.3f}]")

        return {
            "uid": s.uid,
            "surprise": surprise,
            "energy_budget": s.energy_budget,
            "stable": s.meta["surprise_ema"] < 0.5
        }

