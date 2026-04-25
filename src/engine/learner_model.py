import math
import time

from src.models.learner import AttemptRecord, LearnerSkillState, SkillAssessment

DECAY_CONSTANT = 604800  # 1 week in seconds
FORGETTING_DECAY_K = 1 / (60 * 60 * 24 * 90)  # ~90-day slow decay
MIN_CONFIDENCE = 10
MIN_MASTERY = 5
MAX_MASTERY = 100
MAX_VARIANCE = 225
BASE_REVIEW_INTERVAL_SECONDS = 86400.0
MAX_REVIEW_INTERVAL_SECONDS = 86400.0 * 30


def initialize_skill_state(skill_id: str) -> LearnerSkillState:
    """Init new skill (total uncertainty)."""
    now = time.time()
    return LearnerSkillState(
        skill_id=skill_id,
        mastery_mu=50.0,
        mastery_variance=225.0,  # Std dev = 15
        last_updated=now,
        last_seen_timestamp=now,
        review_interval_seconds=BASE_REVIEW_INTERVAL_SECONDS,
        attempt_count=0,
        recent_attempts=[],
    )


def apply_forgetting(state: LearnerSkillState, current_time: float) -> tuple[LearnerSkillState, float]:
    """Apply exponential forgetting based on time since last seen."""
    time_since_last_seen = max(0.0, current_time - state.last_seen_timestamp)
    if time_since_last_seen == 0:
        return state, 0.0

    decayed_mastery = state.mastery_mu * math.exp(-FORGETTING_DECAY_K * time_since_last_seen)
    decayed_mastery = max(MIN_MASTERY, min(MAX_MASTERY, decayed_mastery))
    decay_applied = max(0.0, state.mastery_mu - decayed_mastery)

    return (
        LearnerSkillState(
            skill_id=state.skill_id,
            mastery_mu=decayed_mastery,
            mastery_variance=state.mastery_variance,
            last_updated=state.last_updated,
            last_seen_timestamp=current_time,
            review_interval_seconds=state.review_interval_seconds,
            attempt_count=state.attempt_count,
            recent_attempts=state.recent_attempts,
        ),
        decay_applied,
    )


def is_due_for_review(state: LearnerSkillState, current_time: float) -> bool:
    """Return whether this skill is due for review now."""
    return current_time >= (state.last_seen_timestamp + state.review_interval_seconds)


def time_to_next_review_seconds(state: LearnerSkillState, current_time: float) -> float:
    """Seconds remaining until review is due."""
    return max(0.0, (state.last_seen_timestamp + state.review_interval_seconds) - current_time)


def update_review_interval(current_interval: float, success: bool) -> float:
    """Simple spaced-repetition interval update."""
    if success:
        return min(MAX_REVIEW_INTERVAL_SECONDS, max(BASE_REVIEW_INTERVAL_SECONDS, current_interval) * 2)
    return BASE_REVIEW_INTERVAL_SECONDS


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
        # Allow growth on failure, but keep it controlled.
        new_variance = prior_variance * 1.05
        # Recover confidence slowly even on failures to prevent permanent collapse.
        new_variance = new_variance * 0.99

    new_variance = max(10, min(MAX_VARIANCE, new_variance))

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
    boost = 25 if state.mastery_mu < 20 and attempt.success else 0
    computed_mu = state.mastery_mu + (weighted_success_ratio - 0.5) * 20 + boost
    # Smooth updates to avoid abrupt early jumps.
    new_mu = (0.7 * state.mastery_mu) + (0.3 * computed_mu)
    new_mu = max(MIN_MASTERY, min(MAX_MASTERY, new_mu))

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
        new_variance = min(MAX_VARIANCE, new_variance * 1.1)

    return LearnerSkillState(
        skill_id=state.skill_id,
        mastery_mu=new_mu,
        mastery_variance=new_variance,
        last_updated=now,
        last_seen_timestamp=now,
        review_interval_seconds=update_review_interval(state.review_interval_seconds, attempt.success),
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
