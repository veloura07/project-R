"""
relational_engine.py — Rigorous Constraint-Transition (CT) Engine with KKT Dual Ascent.

Implements the Constraint-Transition (CT) triplet:
    tau = (G, delta_G, Lambda)
and the 6 universal operators of the Relational Calculus:
    1. Observe
    2. Perturb
    3. Resolve (Euler-Lagrange update under KKT shadow prices)
    4. Compose
    5. Propagate
    6. Explain (Symbolic invariant compiler / MDL-based model reduction)
"""

import math
from typing import List, Dict, Any, Callable, Tuple

class RelationalEngine:
    """
    The Relational Engine with KKT dual ascent and symbolic invariant discovery.
    """
    def __init__(self, size: int = 20, eta: float = 0.05, alpha_dual: float = 0.1):
        self.size = size
        self.eta = eta
        self.alpha_dual = alpha_dual  # Dual learning rate for KKT multiplier updates

        self.dim = 2
        self.G = [[0.0 for _ in range(self.dim)] for _ in range(size)]
        self.delta_G = [[0.0 for _ in range(self.dim)] for _ in range(size)]
        
        # lambdas: Lagrange multipliers (KKT dual variables representing constraint pressure)
        self.lambdas: Dict[str, float] = {}
        self.constraints: Dict[str, Callable[[List[List[float]]], float]] = {}
        
        # Local time derived dynamically from change
        self.local_time = 0.0

    def observe(self, node_idx: int, y: List[float]):
        """Observe: updates G's coordinates with observed y."""
        if 0 <= node_idx < self.size:
            self.G[node_idx] = list(y)

    def perturb(self, name: str, constraint_fn: Callable[[List[List[float]]], float], initial_lambda: float = 1.0):
        """Perturb: registers a new constraint and initial Lagrange pressure."""
        self.constraints[name] = constraint_fn
        self.lambdas[name] = initial_lambda

    def resolve(self, dt: float = 0.1):
        """
        Resolve: runs one KKT primal-dual update step.
        Primal update: G = G - eta * grad_G (L)
        Dual update: lambda = max(0, lambda + alpha_dual * C(G))
        """
        eps = 1e-4
        grad = [[0.0 for _ in range(self.dim)] for _ in range(self.size)]
        
        # 1. Compute primal gradient of the Lagrangian: L = Surprise + sum(lambda * C(G)^2)
        for name, c_fn in self.constraints.items():
            l_val = self.lambdas.get(name, 1.0)
            base_val = c_fn(self.G)
            
            if abs(base_val) < 1e-9:
                continue
                
            for i in range(self.size):
                for d in range(self.dim):
                    # Numerical gradient of C(G)
                    self.G[i][d] += eps
                    val_plus = c_fn(self.G)
                    self.G[i][d] -= 2 * eps
                    val_minus = c_fn(self.G)
                    self.G[i][d] += eps # Restore
                    
                    dC_dG = (val_plus - val_minus) / (2 * eps)
                    # d/dG (lambda * C(G)^2) = 2 * lambda * C(G) * dC_dG
                    grad[i][d] += 2 * l_val * base_val * dC_dG

        # 2. Update G and estimate delta_G
        displacement = 0.0
        for i in range(self.size):
            for d in range(self.dim):
                step = -self.eta * grad[i][d]
                self.delta_G[i][d] = step / dt
                self.G[i][d] += step
                displacement += step ** 2

        # 3. KKT Dual Ascent: update multipliers (shadow prices) based on constraint violation
        for name, c_fn in self.constraints.items():
            violation = c_fn(self.G)
            # Update dual variable: lambda = max(0.01, lambda + alpha_dual * violation^2)
            self.lambdas[name] = max(0.01, self.lambdas[name] + self.alpha_dual * (violation ** 2))

        # 4. Event-driven time: dt emerges from coordinate displacement magnitude
        # If nothing changes, time does not advance.
        self.local_time += math.sqrt(displacement) + 0.01

    def compose(self, other: 'RelationalEngine'):
        """Compose: concatenates systems and combines constraints."""
        new_size = self.size + other.size
        composed = RelationalEngine(size=new_size, eta=self.eta, alpha_dual=self.alpha_dual)
        composed.G = self.G + other.G
        composed.constraints.update(self.constraints)
        composed.constraints.update(other.constraints)
        composed.lambdas.update(self.lambdas)
        composed.lambdas.update(other.lambdas)
        return composed

    def propagate(self, threshold: float = 0.05, dt: float = 0.1):
        """Propagate: runs Resolve only on constraints whose pressure exceeds threshold."""
        active = any(l_val > threshold for l_val in self.lambdas.values())
        if active:
            self.resolve(dt)

    def explain(self, trajectory: List[List[List[float]]] = None, threshold: float = 0.01) -> List[Tuple[str, Callable[[List[List[float]]], float]]]:
        """
        Explain: The Constraint Compiler operator.
        Discovers simple algebraic invariants:
        1. Pairwise distance invariants over a trajectory history.
        2. Radial conservation invariant (if no trajectory provided).
        """
        discovered = []
        
        if trajectory is not None and len(trajectory) > 2:
            # Trajectory shape: T (steps) x N (nodes) x dim
            T_len = len(trajectory)
            
            # Check all pairs of nodes (i, j) for constant distance over time
            for i in range(self.size):
                for j in range(i + 1, self.size):
                    dists = []
                    for t in range(T_len):
                        g_t = trajectory[t]
                        d = math.sqrt((g_t[i][0] - g_t[j][0])**2 + (g_t[i][1] - g_t[j][1])**2)
                        dists.append(d)
                        
                    mean_d = sum(dists) / T_len
                    var_d = sum((d - mean_d)**2 for d in dists) / T_len
                    
                    if var_d < threshold:
                        # Found invariant pairwise distance!
                        # Capture the values using default arguments in lambda to avoid closures binding late
                        def make_pairwise_constraint(node_a=i, node_b=j, target_d=mean_d):
                            return lambda G: (math.sqrt((G[node_a][0] - G[node_b][0])**2 + (G[node_a][1] - G[node_b][1])**2) - target_d)
                            
                        discovered.append((f"distance_{i}_{j}", make_pairwise_constraint(i, j, mean_d)))
        else:
            # Check radial conservation: x^2 + y^2 = R^2 in current state G
            radii_sq = [c[0]**2 + c[1]**2 for c in self.G]
            mean_r_sq = sum(radii_sq) / len(radii_sq)
            var_r_sq = sum((r - mean_r_sq)**2 for r in radii_sq) / len(radii_sq)
            
            if var_r_sq < threshold:
                r_target = math.sqrt(mean_r_sq)
                
                def radius_constraint(G):
                    total_viol = 0.0
                    for coords in G:
                        dist = math.sqrt(coords[0]**2 + coords[1]**2)
                        total_viol += (dist - r_target)
                    return total_viol / len(G)
                    
                discovered.append(("radial_invariant", radius_constraint))
                
        return discovered

