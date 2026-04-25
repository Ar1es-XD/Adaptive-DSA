import math
import time

from src.models.learner import AttemptRecord, LearnerSkillState, SkillAssessment
from src.models.problem_state import ProblemState

DECAY_CONSTANT = 604800  # 1 week in seconds
FORGETTING_DECAY_K = 8.5e-7  # ~7% mastery loss over 24h
MIN_CONFIDENCE = 10
MIN_MASTERY = 5
MAX_MASTERY = 100
MAX_VARIANCE = 225
BASE_REVIEW_INTERVAL_SECONDS = 86400.0
MIN_INTERVAL_DAYS = 0.5


def initialize_skill_state(skill_id: str) -> LearnerSkillState:
    """Init new skill (total uncertainty)."""
    now = time.time()
    return LearnerSkillState(
        skill_id=skill_id,
        mastery_mu=50.0,
        mastery_variance=225.0,  # Std dev = 15
        last_updated=now,
        last_seen_timestamp=now,
        repetitions=0,
        ease_factor=2.5,
        interval_days=1.0,
        review_interval_seconds=BASE_REVIEW_INTERVAL_SECONDS,
        attempt_count=0,
        recent_attempts=[],
    )


def initialize_problem_state(problem_id: str, current_time: float | None = None) -> ProblemState:
    """Init per-problem scheduling state."""
    now = current_time if current_time is not None else time.time()
    return ProblemState(problem_id=problem_id, last_seen_timestamp=now)


def apply_forgetting(state: LearnerSkillState, current_time: float) -> tuple[LearnerSkillState, float]:
    """Compute effective mastery decay without mutating review schedule timestamps."""
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
            last_seen_timestamp=state.last_seen_timestamp,
            repetitions=state.repetitions,
            ease_factor=state.ease_factor,
            interval_days=state.interval_days,
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


def is_problem_due_for_review(problem_state: ProblemState, problem_difficulty: float, current_time: float) -> bool:
    """Return whether this specific problem is due now."""
    display_interval = problem_state.interval_days * (1 + problem_difficulty / 10)
    return current_time >= (problem_state.last_seen_timestamp + (display_interval * 86400))


def time_to_problem_review_seconds(problem_state: ProblemState, problem_difficulty: float, current_time: float) -> float:
    """Seconds remaining until this specific problem is due."""
    display_interval = problem_state.interval_days * (1 + problem_difficulty / 10)
    return max(0.0, (problem_state.last_seen_timestamp + (display_interval * 86400)) - current_time)


def sm2_update(
    repetitions: int,
    ease_factor: float,
    interval_days: float,
    quality: int,
) -> tuple[int, float, float]:
    """Apply one SM-2 scheduling update step."""
    if quality < 3:
        return 0, ease_factor, 1.0

    if repetitions == 0:
        interval_days = 1.0
    elif repetitions == 1:
        interval_days = 6.0
    else:
        interval_days = interval_days * ease_factor

    repetitions += 1

    ease_factor = ease_factor + (
        0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    )
    ease_factor = max(1.3, ease_factor)

    return repetitions, ease_factor, interval_days


def _confidence_from_state(state: LearnerSkillState) -> float:
    """Compute confidence score from current state for scheduling decisions."""
    confidence = max(MIN_CONFIDENCE, min(100, 100 - (state.mastery_variance / 2.25)))
    if state.attempt_count < 3:
        confidence = min(confidence, 25)
    if state.attempt_count < 5:
        confidence = min(confidence, 40)
    return confidence


def compute_quality(success: bool, time_spent_seconds: float, confidence: float) -> int:
    """Map attempt outcomes to an SM-2 quality score."""
    if not success:
        return 2

    if time_spent_seconds < 30:
        base_q = 5
    elif time_spent_seconds < 90:
        base_q = 4
    else:
        base_q = 3

    if confidence < 40:
        base_q -= 1
    elif confidence > 70:
        base_q += 1

    return max(2, min(5, base_q))


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
        # Consistent = reduce uncertainty more aggressively
        new_variance = prior_variance * 0.8
    else:
        # Allow slight growth on failure, but keep it controlled.
        new_variance = prior_variance * 1.05

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
        if att.success:
            # Harder successes contribute more mastery evidence.
            score = min(1.0, 0.55 + (att.problem_difficulty / 20.0))
        else:
            # Failing easy problems penalizes more than failing hard ones.
            score = max(0.0, 0.45 - ((11.0 - att.problem_difficulty) / 20.0))
        weighted_sum += score * weight
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
        repetitions=state.repetitions,
        ease_factor=state.ease_factor,
        interval_days=state.interval_days,
        review_interval_seconds=state.review_interval_seconds,
        attempt_count=state.attempt_count + 1,
        recent_attempts=new_recent,
    )


def update_problem_state_schedule(
    problem_state: ProblemState,
    attempt: AttemptRecord,
    confidence: float,
) -> tuple[ProblemState, int]:
    """Apply SM-2 scheduling update for one problem based on attempt outcome."""
    quality = compute_quality(attempt.success, attempt.time_spent_seconds, confidence)
    repetitions, ease_factor, interval_days = sm2_update(
        problem_state.repetitions,
        problem_state.ease_factor,
        problem_state.interval_days,
        quality,
    )
    interval_days = max(MIN_INTERVAL_DAYS, interval_days)

    return (ProblemState(
        problem_id=problem_state.problem_id,
        repetitions=repetitions,
        ease_factor=ease_factor,
        interval_days=interval_days,
        last_seen_timestamp=attempt.timestamp,
    ), quality)


def assess_mastery(state: LearnerSkillState) -> SkillAssessment:
    """Calculate current assessment (NO state mutation)."""
    confidence = max(MIN_CONFIDENCE, min(100, 100 - (state.mastery_variance / 2.25)))
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


def compute_overall_proficiency(states: list[LearnerSkillState]) -> float:
    """Compute weighted cross-skill proficiency using attempts as weights."""
    if not states:
        return 0.0

    weighted_mastery = 0.0
    total_weight = 0
    for state in states:
        weight = max(1, state.attempt_count)
        weighted_mastery += state.mastery_mu * weight
        total_weight += weight

    return round(weighted_mastery / total_weight, 2)
