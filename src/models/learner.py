from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class AttemptRecord(BaseModel):
    """Single problem attempt by a learner."""

    timestamp: float  # Unix timestamp
    problem_id: str
    success: bool
    time_spent_seconds: float
    problem_difficulty: float  # 1-10 (Rasch)
    user_id: str = "default_learner"


class AttemptLog(BaseModel):
    """Logging model for behavioral tracking"""
    id: Optional[int] = None
    timestamp: float
    problem_id: str
    success: bool
    time_spent_seconds: float
    quality: int
    interval_days: float
    confidence: float


class LearnerSkillState(BaseModel):
    """Bayesian model of learner mastery for one skill."""

    skill_id: str
    mastery_mu: float = 50.0  # Mean (0-100)
    mastery_variance: float = 225.0  # Uncertainty
    last_updated: float  # Unix timestamp
    last_seen_timestamp: float
    repetitions: int = 0
    ease_factor: float = 2.5
    interval_days: float = 1.0
    review_interval_seconds: float = 86400.0
    attempt_count: int = 0
    recent_attempts: List[AttemptRecord] = Field(default_factory=list)  # Last 20

    class Config:
        arbitrary_types_allowed = True


class SkillAssessment(BaseModel):
    """Output: current mastery assessment."""

    skill_id: str
    estimated_mastery: float  # 0-100
    confidence: float  # 0-100 (100 - uncertainty_percent)
    ready_to_advance: bool  # mastery > 80 AND confidence > 75
    should_review: bool  # mastery < 50 OR confidence < 40
    next_recommended_difficulty: float  # 1-10


class Problem(BaseModel):
    """DSA problem definition."""

    problem_id: str
    title: str
    description: str
    topic: str  # arrays, dp, graphs, etc.
    difficulty: float  # 1-10
    pattern: str  # binarySearch, twoPointer, dfs, etc.
    expected_output: str
    hints: List[str] = Field(default_factory=list)
    test_cases: list[dict[str, Any]] | None = None
