from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List
from enum import Enum
import random


class KnowledgeState(Enum):
    UNKNOWN = 0
    STRUGGLING = 1
    PRACTICING = 2
    MASTERED = 3


@dataclass
class ConceptAttempt:
    """Single problem attempt on a concept"""
    concept_id: str
    problem_id: str
    timestamp: datetime
    is_correct: bool
    time_spent_seconds: int
    attempt_number: int
    hint_count: int


@dataclass
class ConceptMetrics:
    """Aggregated metrics for one DSA concept"""
    concept_id: str
    knowledge_state: KnowledgeState
    success_rate: float  # 0.0-1.0
    confidence_level: float  # 0.0-1.0, how sure system is about this assessment
    avg_time_per_attempt: float  # seconds
    total_attempts: int
    mastery_threshold: float = 0.80  # 80% correct = mastered
    
    # Time decay
    last_attempt: datetime = field(default_factory=datetime.now)
    decay_factor: float = 0.95  # older attempts matter less


@dataclass
class LearnerProfile:
    """Complete learner knowledge state"""
    learner_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Core state
    concept_metrics: Dict[str, ConceptMetrics] = field(default_factory=dict)
    attempt_history: List[ConceptAttempt] = field(default_factory=list)
    
    # System metadata
    total_problems_attempted: int = 0
    session_count: int = 0
    
    def get_knowledge_state(self, concept_id: str) -> KnowledgeState:
        """Return current knowledge state for a concept"""
        if concept_id not in self.concept_metrics:
            return KnowledgeState.UNKNOWN
        return self.concept_metrics[concept_id].knowledge_state
    
    def get_difficulty_for_concept(self, concept_id: str) -> int:
        """
        Map knowledge state → difficulty level (1-5)
        
        UNKNOWN → 1 (easy intro)
        STRUGGLING → 2 (medium-easy)
        PRACTICING → 3-4 (medium to medium-hard)
        MASTERED → 5 (challenge problems)
        """
        state = self.get_knowledge_state(concept_id)
        mapping = {
            KnowledgeState.UNKNOWN: 1,
            KnowledgeState.STRUGGLING: 2,
            KnowledgeState.PRACTICING: 4,
            KnowledgeState.MASTERED: 5
        }
        return mapping[state]


def update_knowledge_state(
    metrics: ConceptMetrics
) -> KnowledgeState:
    """
    Determine knowledge state from metrics.
    
    Args:
        metrics: Calculated metrics for a concept
    
    Returns:
        Updated KnowledgeState
    
    Rules:
        1. UNKNOWN: total_attempts < 2
        2. STRUGGLING: success_rate < 0.5 AND total_attempts >= 2
        3. MASTERED: success_rate >= 0.80 AND confidence_level >= 0.7
        4. PRACTICING: everything else
    """
    if metrics.total_attempts < 2:
        if metrics.total_attempts == 1 and metrics.success_rate < 0.5:
            return KnowledgeState.STRUGGLING
        return KnowledgeState.UNKNOWN
    
    if metrics.success_rate < 0.5 and metrics.total_attempts >= 2:
        return KnowledgeState.STRUGGLING
        
    if metrics.success_rate >= 0.80 and metrics.confidence_level >= 0.7:
        return KnowledgeState.MASTERED
        
    return KnowledgeState.PRACTICING


def calculate_metric_for_concept(
    attempts: List[ConceptAttempt],
    decay_factor: float = 0.95,
    window_days: int = 30
) -> ConceptMetrics:
    """
    Calculate metrics for one concept from its attempt history.
    
    Args:
        attempts: All attempts on this concept (chronological)
        decay_factor: How fast old attempts lose weight
        window_days: Recency window (ignore older than this)
    
    Returns:
        ConceptMetrics with success_rate, confidence, time data
    """
    if not attempts:
        raise ValueError("Cannot calculate metrics without attempts")
        
    concept_id = attempts[0].concept_id
    # Default behavior is relative to now, but for stable tests relative to the latest valid attempt is safer, or relative to "now".
    # For rigorous adherence to prompt, we will use datetime.now()
    now = datetime.now()
    cutoff_time = now - timedelta(days=window_days)
    
    valid_attempts = [a for a in attempts if a.timestamp >= cutoff_time]
    
    if not valid_attempts:
        # Fall back to returning default metrics if all are too old
        return ConceptMetrics(
            concept_id=concept_id,
            knowledge_state=KnowledgeState.UNKNOWN,
            success_rate=0.0,
            confidence_level=0.0,
            avg_time_per_attempt=0.0,
            total_attempts=len(attempts),
            last_attempt=attempts[-1].timestamp if attempts else now,
            decay_factor=decay_factor
        )

    weighted_correct = 0.0
    total_weight = 0.0
    total_time = 0
    
    for att in valid_attempts:
        days_ago = max(0.0, (now - att.timestamp).total_seconds() / 86400.0)
        
        # Recent attempts (< 7 days) get weight 1.0
        if days_ago < 7:
            weight = 1.0
        else:
            weight = decay_factor ** days_ago
            
        total_weight += weight
        if att.is_correct:
            weighted_correct += weight
            
        total_time += att.time_spent_seconds
        
    success_rate = weighted_correct / total_weight if total_weight > 0 else 0.0
    success_rate = max(0.0, min(1.0, success_rate))
    
    total_attempts = len(valid_attempts)
    confidence_level = min(1.0, total_attempts / 10.0)
    avg_time = total_time / total_attempts if total_attempts > 0 else 0.0
    
    metrics = ConceptMetrics(
        concept_id=concept_id,
        knowledge_state=KnowledgeState.UNKNOWN, # Will be updated downstream
        success_rate=success_rate,
        confidence_level=confidence_level,
        avg_time_per_attempt=avg_time,
        total_attempts=total_attempts,
        last_attempt=valid_attempts[-1].timestamp,
        decay_factor=decay_factor
    )
    
    metrics.knowledge_state = update_knowledge_state(metrics)
    return metrics


def record_attempt(
    profile: LearnerProfile,
    attempt: ConceptAttempt
) -> LearnerProfile:
    """
    Record a problem attempt and update learner profile.
    
    Args:
        profile: Current learner state
        attempt: Single problem attempt data
    
    Returns:
        Updated profile with new metrics
    """
    # 1. Append attempt to history
    profile.attempt_history.append(attempt)
    
    # 2. Recalculate metrics for that concept using ALL history
    concept_id = attempt.concept_id
    concept_attempts = [a for a in profile.attempt_history if a.concept_id == concept_id]
    
    # Sort attempts chronologically
    concept_attempts.sort(key=lambda x: x.timestamp)
    
    metrics = calculate_metric_for_concept(concept_attempts)
    
    # Update profile components
    profile.concept_metrics[concept_id] = metrics
    profile.total_problems_attempted += 1
    profile.updated_at = datetime.now()
    
    return profile


def select_next_concept(
    profile: LearnerProfile,
    available_concepts: List[str],
    strategy: str = "adaptive"
) -> str:
    """
    Choose what concept learner should practice next.
    
    Args:
        profile: Current learner state
        available_concepts: List of all possible concepts
        strategy: "adaptive" (default) or "fixed"
    
    Returns:
        concept_id to practice next
    """
    if not available_concepts:
        raise ValueError("No concepts available")
        
    if strategy != "adaptive":
        return random.choice(available_concepts)
        
    # Group available by state
    struggling = []
    practicing = []
    unknown = []
    mastered = []
    
    for concept_id in available_concepts:
        state = profile.get_knowledge_state(concept_id)
        metrics = profile.concept_metrics.get(concept_id)
        last_time = metrics.last_attempt.timestamp() if metrics else 0.0
        
        tuple_data = (last_time, concept_id)
        if state == KnowledgeState.STRUGGLING:
            struggling.append(tuple_data)
        elif state == KnowledgeState.PRACTICING:
            practicing.append(tuple_data)
        elif state == KnowledgeState.UNKNOWN:
            unknown.append(tuple_data)
        elif state == KnowledgeState.MASTERED:
            mastered.append(tuple_data)
            
    # Sort groups by oldest timestamp (lowest value)
    struggling.sort()
    practicing.sort()
    unknown.sort()
    mastered.sort()
    
    if struggling:
        return struggling[0][1]
    if practicing:
        return practicing[0][1]
    if unknown:
        return unknown[0][1]
    
    return mastered[0][1]
