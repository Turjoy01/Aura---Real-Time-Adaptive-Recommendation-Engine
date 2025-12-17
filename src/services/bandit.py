from typing import List, Dict, Any
import random

class BanditAlgorithm:
    """
    Multi-armed bandit for exploration vs exploitation
    Placeholder for future neural/contextual bandit implementation
    """
    
    @staticmethod
    def select_events_epsilon_greedy(
        candidates: List[Dict[str, Any]],
        count: int,
        epsilon: float = 0.15
    ) -> List[Dict[str, Any]]:
        """
        Epsilon-greedy selection: 85% exploit (highest score), 15% explore (random)
        """
        if len(candidates) <= count:
            return candidates
        
        # Sort by score descending
        sorted_candidates = sorted(
            candidates,
            key=lambda x: x.get("score", 0),
            reverse=True
        )
        
        # Exploit: top scored events
        exploit_count = int(count * (1 - epsilon))
        exploit_events = sorted_candidates[:exploit_count]
        
        # Explore: random events from rest
        remaining = sorted_candidates[exploit_count:]
        explore_count = count - exploit_count
        explore_events = random.sample(
            remaining,
            min(explore_count, len(remaining))
        )
        
        return exploit_events + explore_events
    
    @staticmethod
    def calculate_ucb_score(
        event_score: float,
        total_impressions: int,
        event_clicks: int,
        total_clicks: int,
        exploration_factor: float = 1.41
    ) -> float:
        """
        Upper Confidence Bound (UCB) score for balancing exploration/exploitation
        """
        if total_impressions == 0:
            return 1.0
        
        exploitation = event_score
        exploration = exploration_factor * (
            ((total_clicks / total_impressions) ** 0.5) / (total_impressions ** 0.5)
        )
        
        return exploitation + exploration
