import uuid
from typing import Dict, Set
from RealityOS.kernel.reality_atom import RealityAtom

class WorkingMemory:
    """
    Tracks currently active atoms and their immediate local context.
    Acts like CPU L1 cache / working memory (7 +- 2 chunks, scaled up for agents).
    """
    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        # atom_id -> RealityAtom
        self.cache: Dict[uuid.UUID, RealityAtom] = {}
        # Keep track of active attention scores (derived from energy)
        self.active_atoms: Set[uuid.UUID] = set()

    def touch(self, atom: RealityAtom):
        """Bring an atom into working memory."""
        self.cache[atom.id] = atom
        self.active_atoms.add(atom.id)
        
        # Evict least active if capacity is exceeded
        if len(self.cache) > self.capacity:
            self._evict_least_active()

    def remove(self, atom_id: uuid.UUID):
        if atom_id in self.cache:
            del self.cache[atom_id]
        if atom_id in self.active_atoms:
            self.active_atoms.remove(atom_id)

    def _evict_least_active(self):
        # Sort by energy level (metabolism)
        sorted_atoms = sorted(self.cache.values(), key=lambda a: a.energy)
        if sorted_atoms:
            victim = sorted_atoms[0]
            self.remove(victim.id)
            print(f"  [WorkingMemory] Evicted atom '{victim.semantic_type}' ({victim.id}) to secondary storage.")
