from typing import Dict, List, Callable, Any, Optional

class ActionSequence:
    def __init__(self, name: str, steps: List[str]):
        self.name = name
        self.steps = steps

class ProceduralMemory:
    """
    Procedural Memory stores learned motor programs, skills,
    and action recipes.
    """
    def __init__(self):
        self.skills: Dict[str, ActionSequence] = {}

    def register_skill(self, name: str, steps: List[str]):
        self.skills[name] = ActionSequence(name, steps)

    def get_skill(self, name: str) -> Optional[ActionSequence]:
        return self.skills.get(name, None)
