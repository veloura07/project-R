import uuid
from typing import Dict, List, Tuple
import math
from RealityOS.kernel.reality_atom import Geometry3D

class SpatialIndex:
    """
    A simplified spatial index (like an R-tree or Octree) 
    to efficiently query objects by location.
    """
    def __init__(self):
        # A simple flat dictionary for prototype. 
        # Production would use an Octree or bounding volume hierarchy.
        self.positions: Dict[uuid.UUID, Geometry3D] = {}
        
    def update_position(self, atom_id: uuid.UUID, position: Geometry3D):
        self.positions[atom_id] = position
        
    def remove(self, atom_id: uuid.UUID):
        if atom_id in self.positions:
            del self.positions[atom_id]
            
    def query_radius(self, center: Geometry3D, radius: float) -> List[uuid.UUID]:
        """Find all atoms within a certain radius."""
        results = []
        for atom_id, pos in self.positions.items():
            dist = self._distance(center, pos)
            if dist <= radius:
                results.append(atom_id)
        return results
        
    def _distance(self, p1: Geometry3D, p2: Geometry3D) -> float:
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)
