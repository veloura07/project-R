"""
knowledge_compiler.py — Compresses experience into executable rules.
Implements rule-mining from state trajectories and commits them to Semantic Memory.
"""

import uuid
from typing import List, Dict, Any
from RealityOS.kernel.cognitive_state import CognitiveState
from RealityOS.memory.semantic_memory import SemanticMemory
from RealityOS.kernel.operator_algebra import OperatorAlgebra


class KnowledgeCompiler:
    """
    Analyzes historical trajectories of cognitive states and compiles
    invariants into symbolic rules in Semantic Memory.
    """

    def __init__(self, semantic_memory: SemanticMemory):
        self.semantic_memory = semantic_memory

    def compile_experience(self, concept: str, states: List[CognitiveState]):
        """
        Compresses state histories, extracts stable boundaries,
        and registers them as executable constraints in the KB.
        """
        if not states:
            return

        # Use OperatorAlgebra compression to extract bounding rule
        rule = OperatorAlgebra.Compress(states)

        # Assert compiled fact in Semantic Memory
        self.semantic_memory.assert_fact(
            concept=concept,
            property_name="invariant_bounds",
            value={
                "dimension": rule.dimension,
                "lower": rule.lower,
                "upper": rule.upper
            }
        )
        print(f"  [KnowledgeCompiler] Compiled rule for '{concept}' on dim {rule.dimension}: [{rule.lower:.3f}, {rule.upper:.3f}]")
