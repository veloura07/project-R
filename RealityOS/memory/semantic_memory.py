from typing import Dict, List, Any

class SemanticMemory:
    """
    Semantic Memory stores abstracted facts, concepts, and rules 
    extracted from events, rather than raw episodes.
    
    Example rule: "ceramic objects have high breaking probability on hard surfaces."
    """
    def __init__(self):
        # concept -> property -> value/rules
        self.knowledge: Dict[str, Dict[str, Any]] = {}

    def assert_fact(self, concept: str, property_name: str, value: Any):
        if concept not in self.knowledge:
            self.knowledge[concept] = {}
        self.knowledge[concept][property_name] = value

    def query_fact(self, concept: str, property_name: str) -> Any:
        return self.knowledge.get(concept, {}).get(property_name, None)
