"""
multi_timescale_brain.py — Multi-Timescale Cognitive Loop Scheduler.
Orchestrates Fast, Medium, Slow, and Dream loops across the Cognitive Fabric.
"""

import time
from typing import List, Dict, Any, Callable
from RealityOS.fabric.cognitive_fabric import CognitiveFabric


class MultiTimescaleBrain:
    """
    Coordinates multi-frequency loops inspired by biological brains:
      1. Fast Loop (1-10ms): Spinal/Reflex safety guard updates
      2. Medium Loop (10-1000ms): Tactical reaction-diffusion field updates
      3. Slow Loop (1s+): Prefrontal goal-seeking evolution steps
      4. Dream Loop: Consolidates experiences and extracts symbolic rules
    """

    def __init__(self, fabric: CognitiveFabric):
        self.fabric = fabric
        
        self.last_fast_time = 0.0
        self.last_medium_time = 0.0
        self.last_slow_time = 0.0
        self.last_dream_time = 0.0
        
        # Loop frequencies in seconds
        self.fast_interval = 0.005    # 5ms (200Hz)
        self.medium_interval = 0.05    # 50ms (20Hz)
        self.slow_interval = 0.5       # 500ms (2Hz)
        self.dream_interval = 5.0      # 5s (Consolidation cycle in demo)

    def tick(self, custom_time: float = None):
        """Ticks the brain loops based on elapsed wall-clock or virtual time."""
        current_time = custom_time or time.time()
        
        # 1. FAST LOOP (Reflexive events priority dispatch)
        if current_time - self.last_fast_time >= self.fast_interval:
            self._run_fast_loop()
            self.last_fast_time = current_time
            
        # 2. MEDIUM LOOP (Reaction-diffusion field updates)
        if current_time - self.last_medium_time >= self.medium_interval:
            self._run_medium_loop()
            self.last_medium_time = current_time
            
        # 3. SLOW LOOP (Euler-Lagrange state evolution step)
        if current_time - self.last_slow_time >= self.slow_interval:
            self._run_slow_loop()
            self.last_slow_time = current_time
            
        # 4. DREAM LOOP (Offline compilation & rule extraction)
        if current_time - self.last_dream_time >= self.dream_interval:
            self._run_dream_loop()
            self.last_dream_time = current_time

    def _run_fast_loop(self):
        # Process high-priority events in the fabric queue
        if self.fabric.scheduler.has_events():
            self.fabric.process_tick()

    def _run_medium_loop(self):
        # Step any registered active spatial-temporal cognitive fields
        for field in self.fabric.field_manager.fields.values():
            if hasattr(field, "step"):
                field.step(dt=0.05)

    def _run_slow_loop(self):
        # Evolve intent states using Euler-Lagrange evolution engine
        for cs in list(self.fabric.cognitive_states.values()):
            self.fabric.evolution_engine.step(cs, cs.x)

    def _run_dream_loop(self):
        # Trigger offline consolidation & rule mining
        print("  [Brain/Dream] Executing background memory consolidation...")
        for rt in self.fabric.runtimes:
            rt.dream()
