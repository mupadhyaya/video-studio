import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class MemoryElement:
    content: str
    timestamp: float = field(default_factory=time.time)
    importance_score: float = 1.0

class CognitiveMemoryController:
    """Manages the lifecycle of agentic memories, dividing them into transient STM and consolidated LTM."""
    def __init__(self, stm_capacity: int = 3, consolidation_threshold: float = 0.7):
        self.stm: List[MemoryElement] = []
        self.ltm: List[MemoryElement] = []
        self.stm_capacity = stm_capacity
        self.consolidation_threshold = consolidation_threshold

    def ingest_experience(self, content: str, importance: float) -> Optional[MemoryElement]:
        element = MemoryElement(content=content, importance_score=importance)
        self.stm.append(element)
        print(f"[STM] Ingested raw experience: '{content}'")
        
        if len(self.stm) > self.stm_capacity:
            evicted = self.stm.pop(0)
            print(f"[STM] Capacity exceeded. Evicting oldest element: '{evicted.content}'")
            if evicted.importance_score >= self.consolidation_threshold:
                self.consolidate_to_ltm(evicted)
                return evicted
        return None

    def consolidate_to_ltm(self, element: MemoryElement) -> None:
        print(f"[LTM Consolidation] Promoting high-importance memory to Long-Term Storage: '{element.content}'")
        self.ltm.append(element)