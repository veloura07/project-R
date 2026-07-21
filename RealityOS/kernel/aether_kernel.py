"""
aether_kernel.py — The Unified Aether Core Kernel.
Implements the 5 Primitive Laws of State Computing and the 14 Unix-style API primitives.
"""

import uuid
import time
import copy
import math
from typing import List, Dict, Any, Callable, Tuple, Optional

class AetherEvent:
    """
    Law 1: Everything is an Event.
    Represents the fundamental unit of change and information in Aether.
    """
    def __init__(
        self,
        event_type: str,
        target: Any,
        source: Optional[str] = None,
        delta: Optional[List[float]] = None,
        cause: Optional[uuid.UUID] = None,
        causal_chain: Optional[List[uuid.UUID]] = None
    ):
        self.id = uuid.uuid4()
        self.timestamp = time.time()
        self.event_type = event_type  # "OBSERVATION" | "TRANSITION" | "RELATION" | "CONSTRAINT_GRADUATION"
        self.target = target
        self.source = source
        self.delta = delta
        self.cause = cause
        self.causal_chain = list(causal_chain) if causal_chain else []
        self.precedence: List[uuid.UUID] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "target": str(self.target),
            "source": self.source,
            "delta": self.delta,
            "cause": str(self.cause) if self.cause else None,
            "causal_chain": [str(cid) for cid in self.causal_chain]
        }


class AetherConstraint:
    """
    Law 3: Stable relationships become Constraints.
    Constraints behave like organisms competing for computational metabolism.
    """
    def __init__(
        self,
        name: str,
        violation_fn: Callable[[List[List[float]]], float],
        symbolic_form: str,
        initial_trust: float = 1.0
    ):
        self.name = name
        self.violation_fn = violation_fn
        self.symbolic_form = symbolic_form
        
        # Organism parameters
        self.energy = 1.0                  # Metabolism reservoir
        self.age = 0                       # Steps since birth
        self.activation_frequency = 0      # evaluation frequency under surprise
        self.trust = initial_trust         # KKT dual variable (multiplier/pressure)
        self.mutation_rate = 0.05
        self.fitness = 1.0
        self.history: List[float] = []

    def evaluate_violation(self, G: List[List[float]]) -> float:
        self.age += 1
        try:
            val = self.violation_fn(G)
        except Exception:
            val = 999.0  # High penalty on failure
        self.history.append(abs(val))
        if len(self.history) > 50:
            self.history.pop(0)
            
        if abs(val) > 1e-4:
            self.activation_frequency += 1
            
        # Update fitness: inversely proportional to mean and variance of violations
        mean_v = sum(self.history) / len(self.history)
        var_v = sum((v - mean_v)**2 for v in self.history) / len(self.history)
        self.fitness = 1.0 / (1.0 + mean_v + 5.0 * var_v)
        
        return val


class AetherState:
    """
    Law 4: Constraints bend State.
    Coordinates represent the local equilibrium of forces.
    """
    def __init__(self, name: str, node_idx: int, dim: int = 2):
        self.name = name
        self.node_idx = node_idx
        self.dim = dim
        self.coords = [0.0] * dim
        self.velocity = [0.0] * dim
        
        # Sleep-wake state
        self.active = True
        self.sleep_ticks = 0
        self.energy_budget = 1.0


class AetherUniverse:
    """
    The main Aether Runtime orchestrator.
    Exposes the 14 Unix-style API primitives.
    """
    def __init__(self, size: int = 20, dim: int = 2, eta: float = 0.08, alpha_dual: float = 0.05):
        self.size = size
        self.dim = dim
        self.eta = eta
        self.alpha_dual = alpha_dual
        
        self.states = [AetherState(f"node_{i}", i, dim) for i in range(size)]
        self.constraints: Dict[str, AetherConstraint] = {}
        self.events: List[AetherEvent] = []
        self.relations: Dict[int, List[int]] = {i: [] for i in range(size)} # adjacency representation
        
        # Metrics & Thermodynamics
        self.trajectory_history: List[List[List[float]]] = []
        self.info_gain = 0.0
        self.compute_spent = 0.0
        self.local_time = 0.0
        self.is_initialized = False

    def get_G(self) -> List[List[float]]:
        return [list(s.coords) for s in self.states]

    def set_G(self, G: List[List[float]]):
        for i in range(self.size):
            if i < len(G):
                self.states[i].coords = list(G[i])

    # =========================================================================
    # THE 14 API PRIMITIVES
    # =========================================================================

    def observe(self, node_idx: int, values: List[float]) -> AetherEvent:
        """
        1. observe() — Ingest sensory evidence events into the runtime.
        """
        if node_idx < 0 or node_idx >= self.size:
            raise IndexError("Node index out of range")
        if len(values) != self.dim:
            raise ValueError(f"Expected values of dimension {self.dim}")
            
        old_coords = list(self.states[node_idx].coords)
        self.states[node_idx].coords = list(values)
        
        # Wake up node
        self.states[node_idx].active = True
        self.states[node_idx].sleep_ticks = 0
        
        # Calculate information gain (Shannon reduction under observation entropy)
        diff = sum((values[d] - old_coords[d])**2 for d in range(self.dim))
        self.info_gain += math.log(1.0 + diff)
        
        # Emit Law 1 event
        event = AetherEvent(
            event_type="OBSERVATION",
            target=f"node_{node_idx}",
            delta=[values[d] - old_coords[d] for d in range(self.dim)]
        )
        self.events.append(event)
        return event

    def relate(self, node_a: int, node_b: int, relation_type: str = "coupling") -> AetherEvent:
        """
        2. relate() — Establish topological dependency edges between events/states.
        """
        if node_a < 0 or node_a >= self.size or node_b < 0 or node_b >= self.size:
            raise IndexError("Node index out of range")
            
        if node_b not in self.relations[node_a]:
            self.relations[node_a].append(node_b)
        if node_a not in self.relations[node_b]:
            self.relations[node_b].append(node_a)
            
        event = AetherEvent(
            event_type="RELATION",
            target=f"edge_{node_a}_{node_b}",
            source=f"relate_call",
            delta=[float(node_a), float(node_b)]
        )
        self.events.append(event)
        return event

    def discover(self, threshold: float = 0.02) -> List[AetherEvent]:
        """
        3. discover() — Scans logs/trajectory to compile candidate invariant processes.
        """
        if len(self.trajectory_history) < 5:
            return []
            
        discovered_events = []
        T_len = len(self.trajectory_history)
        
        # Check all related pairs for constant distance invariants
        for i in range(self.size):
            for j in self.relations[i]:
                if j <= i:
                    continue
                    
                name = f"dist_invariant_{i}_{j}"
                if name in self.constraints:
                    continue
                    
                dists = []
                for t in range(T_len):
                    g_t = self.trajectory_history[t]
                    d = math.sqrt(sum((g_t[i][d] - g_t[j][d])**2 for d in range(self.dim)))
                    dists.append(d)
                    
                mean_d = sum(dists) / T_len
                var_d = sum((d - mean_d)**2 for d in dists) / T_len
                
                # Law 3: If variance is below threshold, graduate relation to constraint
                if var_d < threshold:
                    def make_constraint_fn(idx_a=i, idx_b=j, target_dist=mean_d):
                        return lambda G: math.sqrt(sum((G[idx_a][d] - G[idx_b][d])**2 for d in range(len(G[idx_a])))) - target_dist
                        
                    self.constrain(
                        name=name,
                        violation_fn=make_constraint_fn(),
                        symbolic_form=f"||G[{i}] - G[{j}]|| - {mean_d:.3f} = 0"
                    )
                    
                    event = AetherEvent(
                        event_type="CONSTRAINT_GRADUATION",
                        target=name,
                        source="discover_operator"
                    )
                    self.events.append(event)
                    discovered_events.append(event)
                    
        return discovered_events

    def constrain(self, name: str, violation_fn: Callable[[List[List[float]]], float], symbolic_form: str):
        """
        4. constrain() — Append a boundary process onto the state space.
        """
        constraint = AetherConstraint(name, violation_fn, symbolic_form)
        self.constraints[name] = constraint

    def stabilize(self, dt: float = 0.1, gate_threshold: float = 0.01) -> List[AetherEvent]:
        """
        5. stabilize() — Run localized active constraint negotiation to reach equilibrium.
           Nodes negotiate forces, and updates cascade to neighbors.
        """
        eps = 1e-4
        proposals = [[] for _ in range(self.size)]
        G = self.get_G()
        
        # 1. Constraints calculate local forces autonomously
        for name, c in self.constraints.items():
            base_val = c.evaluate_violation(G)
            if abs(base_val) < 1e-9:
                continue
                
            for i in range(self.size):
                grad_node = [0.0] * self.dim
                is_connected = False
                for d in range(self.dim):
                    self.states[i].coords[d] += eps
                    val_plus = c.evaluate_violation(self.get_G())
                    self.states[i].coords[d] -= 2 * eps
                    val_minus = c.evaluate_violation(self.get_G())
                    self.states[i].coords[d] += eps # Restore
                    
                    dC_dG = (val_plus - val_minus) / (2 * eps)
                    if abs(dC_dG) > 1e-5:
                        is_connected = True
                    grad_node[d] = dC_dG
                    
                if is_connected:
                    # force proposal: -2 * lambda * C(G) * dC_dG
                    force = [-2.0 * c.trust * base_val * grad_node[d] for d in range(self.dim)]
                    proposals[i].append((force, name))
                    
                    # Law 5: Cascade wakes up node if proposed force is significant
                    force_mag = math.sqrt(sum(f**2 for f in force))
                    if force_mag > 1e-4:
                        if not self.states[i].active:
                            self.states[i].active = True
                            self.states[i].sleep_ticks = 0
                            
        # 2. Local node-level brokerage updates
        displacement = 0.0
        violations = [abs(c.evaluate_violation(G)) for c in self.constraints.values()]
        max_viol = max(violations) if violations else 0.0
        adaptive_eta = self.eta * (1.0 + min(2.0, max_viol))
        
        cascade_events = []
        
        for i in range(self.size):
            if not self.states[i].active:
                self.states[i].sleep_ticks += 1
                continue
                
            # Local negotiation sum
            net_force = [0.0] * self.dim
            for force, name in proposals[i]:
                for d in range(self.dim):
                    net_force[d] += force[d]
                    
            node_displacement = 0.0
            old_coords = list(self.states[i].coords)
            
            for d in range(self.dim):
                step = adaptive_eta * net_force[d]
                self.states[i].velocity[d] = step / dt
                self.states[i].coords[d] += step
                node_displacement += step**2
                
            displacement += node_displacement
            self.compute_spent += float(self.dim * (len(proposals[i]) + 1))
            
            # Law 5: Coordinate adjustments emit transition events
            mag = math.sqrt(node_displacement)
            if mag > gate_threshold:
                self.states[i].sleep_ticks = 0
                event = AetherEvent(
                    event_type="TRANSITION",
                    target=f"node_{i}",
                    delta=[self.states[i].coords[d] - old_coords[d] for d in range(self.dim)]
                )
                self.events.append(event)
                cascade_events.append(event)
            else:
                self.states[i].sleep_ticks += 1
                if self.states[i].sleep_ticks >= 5:
                    self.states[i].active = False
                    
        # 3. Evolve dual Lagrange values
        for name, c in self.constraints.items():
            viol = c.evaluate_violation(self.get_G())
            c.trust = max(0.01, c.trust + self.alpha_dual * (viol**2))
            
        # 4. Advance event-driven intrinsic time
        self.local_time += math.sqrt(displacement) + 0.01
        
        # Log history
        self.trajectory_history.append(self.get_G())
        if len(self.trajectory_history) > 100:
            self.trajectory_history.pop(0)
            
        return cascade_events

    def predict(self, steps: int = 5, dt: float = 0.1) -> List[List[List[float]]]:
        """
        6. predict() — Calculates forward trajectories along vector fields.
        """
        traj = []
        G_temp = self.get_G()
        
        # Simple linear velocity projection for baseline predict
        current_G = copy.deepcopy(G_temp)
        for _ in range(steps):
            next_G = []
            for i in range(self.size):
                next_coords = [current_G[i][d] + self.states[i].velocity[d] * dt for d in range(self.dim)]
                next_G.append(next_coords)
            traj.append(next_G)
            current_G = next_G
        return traj

    def simulate(self, steps: int = 5, dt: float = 0.1) -> List[List[List[float]]]:
        """
        7. simulate() — Project future trajectories on counterfactual branched timelines.
        """
        cloned = self.fork()
        trajectory = []
        for _ in range(steps):
            cloned.stabilize(dt)
            trajectory.append(cloned.get_G())
        return trajectory

    def fork(self) -> 'AetherUniverse':
        """
        8. fork() — Deep clone the state, relationships, and constraints.
        """
        cloned = AetherUniverse(size=self.size, dim=self.dim, eta=self.eta, alpha_dual=self.alpha_dual)
        cloned.relations = copy.deepcopy(self.relations)
        cloned.info_gain = self.info_gain
        cloned.compute_spent = self.compute_spent
        cloned.local_time = self.local_time
        cloned.trajectory_history = copy.deepcopy(self.trajectory_history)
        
        # Clone states
        for i in range(self.size):
            cloned.states[i].coords = list(self.states[i].coords)
            cloned.states[i].velocity = list(self.states[i].velocity)
            cloned.states[i].active = self.states[i].active
            cloned.states[i].sleep_ticks = self.states[i].sleep_ticks
            
        # Clone constraints
        for name, c in self.constraints.items():
            cloned.constraints[name] = AetherConstraint(name, c.violation_fn, c.symbolic_form)
            cloned.constraints[name].trust = c.trust
            cloned.constraints[name].energy = c.energy
            cloned.constraints[name].fitness = c.fitness
            cloned.constraints[name].history = list(c.history)
            
        return cloned

    def merge(self, other: 'AetherUniverse') -> 'AetherUniverse':
        """
        9. merge() — Fuses two branched universes.
        """
        merged_size = self.size + other.size
        merged = AetherUniverse(size=merged_size, dim=self.dim, eta=self.eta, alpha_dual=self.alpha_dual)
        
        # Copy states from self
        for i in range(self.size):
            merged.states[i].coords = list(self.states[i].coords)
            merged.states[i].velocity = list(self.states[i].velocity)
            merged.states[i].active = self.states[i].active
            
        # Copy states from other (shifted by self.size)
        for i in range(other.size):
            target_idx = self.size + i
            merged.states[target_idx].coords = list(other.states[i].coords)
            merged.states[target_idx].velocity = list(other.states[i].velocity)
            merged.states[target_idx].active = other.states[i].active
            
        # Merge relationships
        for node, adj in self.relations.items():
            merged.relations[node] = list(adj)
        for node, adj in other.relations.items():
            target_node = self.size + node
            merged.relations[target_node] = [self.size + neighbor for neighbor in adj]
            
        # Merge constraints
        for name, c in self.constraints.items():
            merged.constraints[name] = AetherConstraint(name, c.violation_fn, c.symbolic_form, initial_trust=c.trust)
        for name, c in other.constraints.items():
            # Shift node access indices inside constraints if necessary (represented via modified violation)
            def make_shifted_violation(old_fn=c.violation_fn, offset=self.size):
                return lambda G: old_fn(G[offset:])
            merged.constraints[f"merged_{name}"] = AetherConstraint(f"merged_{name}", make_shifted_violation(), c.symbolic_form, initial_trust=c.trust)
            
        return merged

    def rollback(self, ticks: int):
        """
        10. rollback() — Rewinds coordinate history to previous event frames.
        """
        if len(self.trajectory_history) < ticks:
            raise RuntimeError("Insufficient history to rollback.")
        target_state = self.trajectory_history[-ticks]
        self.set_G(target_state)
        self.trajectory_history = self.trajectory_history[:-ticks]
        
        # Wake up all nodes on rollback
        for s in self.states:
            s.active = True
            s.sleep_ticks = 0

    def forget(self, rate: float = 0.05):
        """
        11. forget() — Decays the trust (Lagrange multiplier) of active constraints.
        """
        for c in self.constraints.values():
            c.trust = max(0.01, c.trust * (1.0 - rate))

    def compress(self, threshold: float = 0.05) -> List[Tuple[int, float, float]]:
        """
        12. compress() — Compresses trajectory events into generalized macro bounding rules.
        """
        if len(self.trajectory_history) < 2:
            return []
            
        bounds = []
        for i in range(self.size):
            coords_d0 = [g[i][0] for g in self.trajectory_history]
            mean_c = sum(coords_d0) / len(coords_d0)
            var_c = sum((c - mean_c)**2 for c in coords_d0) / len(coords_d0)
            
            # If coordinates are stable, compress to a bounding range constraint
            if var_c < threshold:
                min_c, max_c = min(coords_d0), max(coords_d0)
                bounds.append((i, min_c - 0.1, max_c + 0.1))
                
        return bounds

    def evolve(self, dt: float = 0.1):
        """
        13. evolve() — Steps constraint genomes, updates fitness, and depletes constraint energy.
        """
        G = self.get_G()
        dead_names = []
        
        for name, c in self.constraints.items():
            c.evaluate_violation(G)
            
            # Metabolic consumption: energy declines over time, but is restored by useful constraints
            # (i.e. those that have a high trust/pressure, indicating they are necessary invariants)
            c.energy = max(0.0, c.energy - 0.02 + 0.05 * c.trust)
            
            # Selection: Prune constraints that have zero energy or extremely poor fitness
            if c.energy <= 0.0 or (c.age > 20 and c.fitness < 0.1):
                dead_names.append(name)
                
        for name in dead_names:
            self.constraints.pop(name)
            event = AetherEvent("CONSTRAINT_DEATH", target=name, source="evolve_operator")
            self.events.append(event)

    def measure(self) -> Dict[str, float]:
        """
        14. measure() — Query potential energy, entropy, and metabolic efficiency.
        """
        G = self.get_G()
        
        # 1. Potential Energy: sum of constraint penalties
        potential = 0.0
        for name, c in self.constraints.items():
            viol = c.evaluate_violation(G)
            potential += c.trust * (viol**2)
            
        # 2. Constraint Entropy: H = -sum(p * log(p)) measuring constraint conflicts
        entropy = 0.0
        pressures = []
        for name, c in self.constraints.items():
            viol = abs(c.evaluate_violation(G))
            pressures.append(c.trust * viol)
            
        sum_pressures = sum(pressures)
        if sum_pressures > 1e-9:
            for p_val in pressures:
                p_norm = p_val / sum_pressures
                if p_norm > 1e-9:
                    entropy -= p_norm * math.log(p_norm)
                    
        # 3. Metabolic efficiency: Information gained per unit of compute spent
        metabolism = self.info_gain / (self.compute_spent + 1e-10)
        
        return {
            "energy_spent": self.compute_spent,
            "potential_energy": potential,
            "entropy": entropy,
            "information_gain": self.info_gain,
            "metabolism": metabolism
        }
