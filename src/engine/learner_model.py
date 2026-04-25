import math
import time

from src.models.learner import AttemptRecord, LearnerSkillState, SkillAssessment

DECAY_CONSTANT = 604800  # 1 week in seconds
MIN_CONFIDENCE = 10
MAX_MASTERY = 100


def initialize_skill_state(skill_id: str) -> LearnerSkillState:
    """Init new skill (total uncertainty)."""
    return LearnerSkillState(
        skill_id=skill_id,
        mastery_mu=50.0,
        mastery_variance=225.0,  # Std dev = 15
        last_updated=time.time(),
        attempt_count=0,
        recent_attempts=[],
    )


def decay_factor(attempt_timestamp: float, current_time: float) -> float:
    """Exponential decay: older = less weight."""
    age_seconds = current_time - attempt_timestamp
    return math.exp(-age_seconds / DECAY_CONSTANT)


def bayesian_update(
    prior_mu: float,
    prior_variance: float,
    success: bool,
    problem_difficulty: float,
) -> tuple[float, float]:
    """
    Bayesian update: success/failure on difficulty-N problem.

    Returns: (new_mu, new_variance)
    """
    # Likelihood shift based on difficulty
    success_shift = 10 if success else -10
    difficulty_multiplier = problem_difficulty / 5.0

    # Update mean
    new_mu = prior_mu + (success_shift * difficulty_multiplier)
    new_mu = max(0, min(MAX_MASTERY, new_mu))

    # Update variance (confidence)
    if success:
        # Consistent = reduce uncertainty
        new_variance = prior_variance * 0.85
    else:
        # Inconsistent = increase uncertainty
        new_variance = prior_variance * 1.1

    new_variance = max(10, new_variance)  # Min uncertainty

    return new_mu, new_variance


def record_attempt(state: LearnerSkillState, attempt: AttemptRecord) -> LearnerSkillState:
    """Record attempt and return UPDATED state (immutable)."""
    now = attempt.timestamp

    # Add to recent attempts
    new_recent = state.recent_attempts + [attempt]
    if len(new_recent) > 20:
        new_recent = new_recent[-20:]  # Keep last 20

    # Recalculate mastery with decay
    weighted_sum = 0
    weight_total = 0

    for att in new_recent:
        weight = decay_factor(att.timestamp, now)
        weighted_sum += (1 if att.success else 0) * weight * (att.problem_difficulty / 5.0)
        weight_total += weight

    weighted_success_ratio = weighted_sum / weight_total if weight_total > 0 else 0.5
    computed_mu = state.mastery_mu + (weighted_success_ratio - 0.5) * 20
    # Smooth updates to avoid abrupt early jumps.
    new_mu = (0.7 * state.mastery_mu) + (0.3 * computed_mu)
    new_mu = max(0, min(MAX_MASTERY, new_mu))

    # Bayesian variance update
    _, variance_delta = bayesian_update(
        state.mastery_variance,
        state.mastery_variance,
        attempt.success,
        attempt.problem_difficulty,
    )
    new_variance = variance_delta

    # If gap since last update > 7 days, increase uncertainty
    days_since_update = (now - state.last_updated) / 86400
    if days_since_update > 7:
        new_variance = min(225, new_variance * 1.3)

    return LearnerSkillState(
        skill_id=state.skill_id,
        mastery_mu=new_mu,
        mastery_variance=new_variance,
        last_updated=now,
        attempt_count=state.attempt_count + 1,
        recent_attempts=new_recent,
    )


def assess_mastery(state: LearnerSkillState) -> SkillAssessment:
    """Calculate current assessment (NO state mutation)."""
    confidence = max(0, min(100, 100 - (state.mastery_variance / 2.25)))
    if state.attempt_count < 3:
        confidence = min(confidence, 25)
    if state.attempt_count < 5:
        confidence = min(confidence, 40)
    ready_to_advance = state.mastery_mu > 80 and confidence > 75
    should_review = state.mastery_mu < 50 or confidence < 40

    # Recommend difficulty based on mastery
    if state.mastery_mu < 40:
        next_difficulty = 2.0
    elif state.mastery_mu < 60:
        next_difficulty = 4.0
    elif state.mastery_mu < 75:
        next_difficulty = 6.0
    elif state.mastery_mu < 90:
        next_difficulty = 7.5
    else:
        next_difficulty = 9.0

    return SkillAssessment(
        skill_id=state.skill_id,
        estimated_mastery=round(state.mastery_mu, 2),
        confidence=round(confidence, 2),
        ready_to_advance=ready_to_advance,
        should_review=should_review,
        next_recommended_difficulty=round(next_difficulty, 1),
    )
