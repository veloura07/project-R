import uuid
from typing import Dict, List, Set, Optional
from RealityOS.kernel.reality_atom import RealityAtom

class RelationEngine:
    """
    Manages the graph topology of the RealityOS universe.
    Allows for querying and traversing relations between atoms.
    """
    def __init__(self):
        # We index atoms by ID for quick traversal
        # In a real system, this would be a distributed graph database
        self.atoms: Dict[uuid.UUID, RealityAtom] = {}
        
    def register_atom(self, atom: RealityAtom):
        self.atoms[atom.id] = atom
        
    def unregister_atom(self, atom_id: uuid.UUID):
        if atom_id in self.atoms:
            del self.atoms[atom_id]
            
    def add_relation(self, source_id: uuid.UUID, target_id: uuid.UUID, relation_type: str):
        if source_id in self.atoms and target_id in self.atoms:
            self.atoms[source_id].add_relation(relation_type, target_id)
            
    def get_neighbors(self, atom_id: uuid.UUID, relation_type: Optional[str] = None) -> Set[uuid.UUID]:
        """Get neighboring atoms, optionally filtered by relation type."""
        if atom_id not in self.atoms:
            return set()
            
        atom = self.atoms[atom_id]
        if relation_type:
            return atom.relations.edges.get(relation_type, set())
        else:
            all_neighbors = set()
            for targets in atom.relations.edges.values():
                all_neighbors.update(targets)
            return all_neighbors
            
    def get_subgraph(self, root_id: uuid.UUID, max_depth: int = 2) -> Dict[uuid.UUID, RealityAtom]:
        """Extract a local subgraph around a root atom."""
        subgraph = {}
        visited = set()
        queue = [(root_id, 0)]
        
        while queue:
            current_id, depth = queue.pop(0)
            if current_id in visited or depth > max_depth:
                continue
                
            visited.add(current_id)
            if current_id in self.atoms:
                subgraph[current_id] = self.atoms[current_id]
                
                for neighbor_id in self.get_neighbors(current_id):
                    queue.append((neighbor_id, depth + 1))
                    
        return subgraph
