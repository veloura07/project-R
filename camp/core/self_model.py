"""
self_model.py — System self-monitoring and health engine for CAMP.

Implements a dedicated self-model using AdaptiveInteraction (AIx) to monitor
the health of the CAMP observability service itself.
"""

import time
import os
from typing import Dict, Any
from RealityOS.kernel.adaptive_interaction import AdaptiveInteraction
from RealityOS.kernel.evolution import DecentralizedEvolution
from RealityOS.kernel.calculus import Calculus


class SelfModel:
    def __init__(self, uid: str = "camp_system"):
        self.evolution_engine = DecentralizedEvolution(eta_base=0.05)
        
        # State vector representation for the system:
        # z_a[0] = memory_usage_mb
        # z_a[1] = event_queue_depth
        # z_a[2] = ticks_per_second
        # z_a[3] = alerts_raised_total
        self.ix = AdaptiveInteraction(
            state_a_id="system_metrics",
            state_b_id="system_limits",
            dim=4,
            uid=uid,
            capacity=1.0  # System model has maximum capacity
        )
        
        # Constraints: memory ceiling at 512MB, queue depth ceiling at 1000
        def memory_constraint(z: List[float]) -> float:
            return 10.0 * (max(0.0, z[0] - 512.0) ** 2)
            
        def queue_constraint(z: List[float]) -> float:
            return 5.0 * (max(0.0, z[1] - 1000.0) ** 2)
            
        Calculus.Constrain(self.ix, memory_constraint)
        Calculus.Constrain(self.ix, queue_constraint)
        
        # Set initial limits metadata
        self.ix.meta["constraints"] = [
            {"name": "memory_limit", "upper": 512.0},
            {"name": "queue_limit", "upper": 1000.0}
        ]
        
        self.start_time = time.time()
        self.tick_count = 0

    def get_system_metrics(self, queue_depth: int, alerts_count: int) -> Dict[str, Any]:
        """Collect current system status metrics."""
        self.tick_count += 1
        
        # Estimate memory usage
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_mb = process.memory_info().rss / (1024 * 1024)
        except ImportError:
            # Fallback mock memory estimation
            mem_mb = 42.5 + (self.tick_count % 10) * 0.1
            
        elapsed = time.time() - self.start_time
        ticks_per_sec = self.tick_count / max(1.0, elapsed)

        obs_a = [mem_mb, float(queue_depth), ticks_per_sec, float(alerts_count)]
        obs_b = [mem_mb * 0.9, float(queue_depth) * 0.9, ticks_per_sec, float(alerts_count)]
        
        # Evolve system self-state
        Calculus.Observe(self.ix, obs_a, obs_b, confidence=1.0, source="self_model")
        self.evolution_engine.step(self.ix)

        # Meta flags update
        self.ix.meta["uptime"] = elapsed
        self.ix.meta["stable"] = mem_mb < 256.0 and queue_depth < 100

        # Return UI compatible telemetry
        return {
            "uptime": elapsed,
            "memory_mb": mem_mb,
            "queue_depth": queue_depth,
            "ticks_per_sec": ticks_per_sec,
            "alerts_raised": alerts_count,
            "system_state": {
                "uid": self.ix.uid,
                "x": list(self.ix.z_a),
                "belief": list(self.ix.z_b),
                "surprise": self.ix.meta.get("surprise", 0.0),
                "energy": self.ix.capacity,
                "tau": list(self.ix.precision),
                "timestamp": time.time(),
                "version": len(self.ix.evidence)
            }
        }
