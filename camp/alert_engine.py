"""
alert_engine.py — Alert engine for CAMP adapted for Adaptive Interactions (AIx).

Surfaces alerts only when the momentum-smoothed state coordinate (z_b)
violates constraint limits.
"""

import time
import heapq
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
from RealityOS.kernel.adaptive_interaction import AdaptiveInteraction


@dataclass(order=True)
class Alert:
    priority: float = field(compare=True)
    agent_id: str = field(compare=False)
    metric: str = field(compare=False)
    message: str = field(compare=False)
    value: float = field(compare=False)
    limit: float = field(compare=False)
    timestamp: float = field(compare=False, default_factory=time.time)
    resolved: bool = field(compare=False, default=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "priority": abs(self.priority),
            "agent_id": self.agent_id,
            "metric": self.metric,
            "message": self.message,
            "value": self.value,
            "limit": self.limit,
            "timestamp": self.timestamp,
            "resolved": self.resolved
        }


class AlertEngine:
    def __init__(self, alert_budget_per_tick: int = 5):
        self.alert_budget_per_tick = alert_budget_per_tick
        self.alert_history: List[Alert] = []
        self.active_alerts: Dict[Tuple[str, str], Alert] = {}

    def check_agent(self, ix: AdaptiveInteraction) -> List[Alert]:
        """Check smoothed target coordinate z_b against metadata constraints."""
        tick_alerts = []
        metric_names = ["cost", "latency", "error_rate", "tokens"]
        
        constraints_list = ix.meta.get("constraints", [])
        for dim, c in enumerate(constraints_list):
            if dim >= len(ix.z_b) or dim >= len(metric_names):
                continue
                
            val = ix.z_b[dim] # z_b represents the smoothed coordinate
            limit = c["upper"]
            
            if val > limit:
                metric_name = metric_names[dim]
                surprise_factor = (val - limit) / (limit if limit > 0 else 1.0)
                # priority = capacity (importance) * surprise
                priority_score = ix.capacity * (1.0 + surprise_factor)
                
                msg = f"Agent '{ix.uid}' {metric_name} exceeded threshold: {val:.3f} > {limit:.3f}"
                
                alert = Alert(
                    priority=-priority_score,
                    agent_id=ix.uid,
                    metric=metric_name,
                    message=msg,
                    value=val,
                    limit=limit
                )
                tick_alerts.append(alert)
                
        return tick_alerts

    def process_tick_alerts(self, agents: List[AdaptiveInteraction]) -> List[Alert]:
        candidates: List[Alert] = []
        for agent in agents:
            candidates.extend(self.check_agent(agent))

        heapq.heapify(candidates)

        surfaced_alerts = []
        processed_count = 0
        
        while candidates and processed_count < self.alert_budget_per_tick:
            alert = heapq.heappop(candidates)
            key = (alert.agent_id, alert.metric)
            
            self.active_alerts[key] = alert
            self.alert_history.append(alert)
            surfaced_alerts.append(alert)
            processed_count += 1

        resolved_keys = []
        active_keys = {(a.agent_id, a.metric) for a in surfaced_alerts}
        for key, active_alert in self.active_alerts.items():
            if key not in active_keys:
                active_alert.resolved = True
                resolved_keys.append(key)
                
        for key in resolved_keys:
            del self.active_alerts[key]

        return surfaced_alerts

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        sorted_history = sorted(self.alert_history, key=lambda a: a.timestamp, reverse=True)
        return [a.to_dict() for a in sorted_history[:limit]]
