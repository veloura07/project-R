import uuid
import time
from enum import Enum
from typing import Dict
from RealityOS.kernel.reality_atom import RealityAtom, Timestamp

class EnergyState(Enum):
    DEEP_SLEEP = "deep_sleep" # Compute: 0, memory: summary. Wakes on external event.
    DORMANT = "dormant"       # Compute: 0, memory: cached. Wakes on field activity.
    IDLE = "idle"             # Compute: minimal, memory: full. Wakes on neighbor activity.
    ALERT = "alert"           # Compute: moderate, memory: full. Active monitoring.
    ACTIVE = "active"         # Compute: full, memory: full. Processing transitions.

class EnergyManager:
    """
    Manages the 'metabolism' of RealityOS.
    Dynamically adjusts computational budgets and states for atoms 
    based on activity, relevance, and global limits.
    """
    def __init__(self, max_energy_budget: float = 1000.0):
        self.max_energy_budget = max_energy_budget
        self.atom_states: Dict[uuid.UUID, EnergyState] = {}
        
    def register_atom(self, atom: RealityAtom):
        self.atom_states[atom.id] = EnergyState.IDLE
        atom.energy = 1.0

    def unregister_atom(self, atom_id: uuid.UUID):
        if atom_id in self.atom_states:
            del self.atom_states[atom_id]

    def record_activity(self, atom: RealityAtom, magnitude: float, timestamp: Timestamp):
        """Boosts an atom's energy when it receives an event."""
        boost = magnitude * 10.0
        atom.energy = min(atom.energy + boost, 100.0)
        atom.last_active = timestamp
        self._update_energy_state(atom)

    def decay_metabolism(self, atom: RealityAtom, elapsed_time: float):
        """Dissipates energy over time to simulate energy decay (calming down)."""
        decay = atom.decay_rate * elapsed_time * 10.0
        atom.energy = max(atom.energy - decay, 0.0)
        self._update_energy_state(atom)

    def _update_energy_state(self, atom: RealityAtom):
        """Maps energy value to structural EnergyState."""
        if atom.energy > 80.0:
            state = EnergyState.ACTIVE
        elif atom.energy > 40.0:
            state = EnergyState.ALERT
        elif atom.energy > 10.0:
            state = EnergyState.IDLE
        elif atom.energy > 1.0:
            state = EnergyState.DORMANT
        else:
            state = EnergyState.DEEP_SLEEP
            
        self.atom_states[atom.id] = state

    def get_state(self, atom_id: uuid.UUID) -> EnergyState:
        return self.atom_states.get(atom_id, EnergyState.DEEP_SLEEP)
        
    def optimize_budget(self, atoms: Dict[uuid.UUID, RealityAtom]):
        """
        Global optimization: If sum(energy) exceeds max_energy_budget,
        forcibly scale down the energy of the least important / lowest confidence atoms.
        """
        total_energy = sum(atom.energy for atom in atoms.values())
        if total_energy <= self.max_energy_budget:
            return
            
        # Scale back dynamically
        scale_factor = self.max_energy_budget / total_energy
        for atom in atoms.values():
            atom.energy *= scale_factor
            self._update_energy_state(atom)
        print(f"  [EnergyManager] Global budget exceeded! Scaled energies by {scale_factor:.2f}")
