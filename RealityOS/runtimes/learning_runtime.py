"""
learning_runtime.py — Continuous online learning and rule extraction.
Subclasses IntelligenceRuntime to analyze and compile observations into knowledge.
"""

import uuid
from typing import List, Dict, Any
from RealityOS.runtimes.base_runtime import IntelligenceRuntime
from RealityOS.kernel.event_engine import Event, EventType
from RealityOS.kernel.reality_atom import Future
from RealityOS.kernel.cognitive_state import CognitiveState
from RealityOS.fabric.knowledge_compiler import KnowledgeCompiler
from RealityOS.memory.semantic_memory import SemanticMemory


class LearningRuntime(IntelligenceRuntime):
    """
    Intelligence Runtime that monitors state updates, maintains history,
    and runs the KnowledgeCompiler to mine invariants and rules.
    """

    def __init__(self, semantic_memory: SemanticMemory):
        super().__init__("LearningRuntime")
        self.compiler = KnowledgeCompiler(semantic_memory)
        
        # concept/type_tag -> list of historical cognitive states observed
        self.history_buffers: Dict[str, List[CognitiveState]] = {}
        self.trigger_threshold = 5  # Compile rule after 5 samples

    def accepts(self, event: Event) -> bool:
        # We accept observations or state transition events
        return event.event_type in (EventType.SENSOR_OBSERVATION, EventType.STATE_TRANSITION)

    def process(self, event: Event, context: Any) -> List[Event]:
        """
        Record observations of cognitive states and trigger rule compilation
        when enough historical samples are accumulated.
        """
        # Context is the dict of all registered atoms/states
        atoms = context
        target_state = atoms.get(event.target)
        
        if not target_state or not hasattr(target_state, "type_tag"):
            return []

        concept = target_state.type_tag
        if concept == "unknown":
            concept = getattr(target_state, "semantic_type", "unknown")

        if concept == "unknown":
            return []

        # Buffer a clone of the state to capture its x value at this point in time
        if concept not in self.history_buffers:
            self.history_buffers[concept] = []

        # Clone state for history compilation
        state_snapshot = CognitiveState(
            uid=f"{target_state.uid}_snap_{len(self.history_buffers[concept])}",
            x=list(target_state.x),
            value=target_state.value,
            type_tag=concept
        )
        self.history_buffers[concept].append(state_snapshot)

        # Trigger compilation if we hit threshold
        if len(self.history_buffers[concept]) >= self.trigger_threshold:
            print(f"  [LearningRuntime] Triggering rule compilation for '{concept}'...")
            self.compiler.compile_experience(concept, self.history_buffers[concept])
            
            # Clear buffer to start accumulating next set of rules/invariants
            self.history_buffers[concept].clear()

        return []

    def predict(self, atom_id: uuid.UUID, horizon: float) -> List[Future]:
        return []
