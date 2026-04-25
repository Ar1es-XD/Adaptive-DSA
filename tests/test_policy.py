import time

from src.engine.policy import select_next_problem
from src.models.learner import LearnerSkillState, Problem, SkillAssessment
from src.models.problem_state import ProblemState


def _problems():
    return [
        Problem(
            problem_id="easy",
            title="Easy",
            description="desc",
            topic="arrays",
            difficulty=2,
            pattern="twoPointer",
            expected_output="ok",
            hints=["h1", "h2"],
        ),
        Problem(
            problem_id="near",
            title="Near",
            description="desc",
            topic="arrays",
            difficulty=4,
            pattern="twoPointer",
            expected_output="ok",
            hints=["h1", "h2"],
        ),
        Problem(
            problem_id="far",
            title="Far",
            description="desc",
            topic="arrays",
            difficulty=9,
            pattern="twoPointer",
            expected_output="ok",
            hints=["h1", "h2"],
        ),
    ]


def _assessment():
    return SkillAssessment(
        skill_id="arrays",
        estimated_mastery=60,
        confidence=50,
        ready_to_advance=False,
        should_review=False,
        next_recommended_difficulty=4,
    )


def _low_confidence_assessment():
    return SkillAssessment(
        skill_id="arrays",
        estimated_mastery=60,
        confidence=25,
        ready_to_advance=False,
        should_review=True,
        next_recommended_difficulty=4,
    )


def test_select_next_problem_prefers_difficulty_window(monkeypatch):
    monkeypatch.setattr("src.engine.policy.random.random", lambda: 0.5)
    monkeypatch.setattr("src.engine.policy.random.choice", lambda seq: seq[0])

    selected = select_next_problem(_assessment(), _problems())
    assert abs(selected.difficulty - 4) <= 1


def test_select_next_problem_exploration_can_choose_full_pool(monkeypatch):
    monkeypatch.setattr("src.engine.policy.random.random", lambda: 0.95)
    monkeypatch.setattr("src.engine.policy.random.choice", lambda seq: seq[-1])

    selected = select_next_problem(_assessment(), _problems())
    assert selected.problem_id == "far"


def test_select_next_problem_prioritizes_due_review(monkeypatch):
    now = time.time()
    state = LearnerSkillState(
        skill_id="arrays",
        mastery_mu=35.0,
        mastery_variance=120.0,
        last_updated=now - 100,
        last_seen_timestamp=now - 100,
        review_interval_seconds=86400.0,
        attempt_count=5,
        recent_attempts=[],
    )
    problem_states = {
        "near": ProblemState(
            problem_id="near",
            repetitions=2,
            ease_factor=2.5,
            interval_days=1.0,
            last_seen_timestamp=now - (86400 * 2),
        )
    }
    monkeypatch.setattr("src.engine.policy.random.choice", lambda seq: seq[0])

    selected = select_next_problem(
        _assessment(),
        _problems(),
        state=state,
        current_time=now,
        problem_states=problem_states,
    )
    assert selected.problem_id == "near"


def test_select_next_problem_biases_review_when_low_confidence(monkeypatch):
    state = None
    monkeypatch.setattr("src.engine.policy.random.random", lambda: 0.1)
    monkeypatch.setattr("src.engine.policy.random.choice", lambda seq: seq[0])

    selected = select_next_problem(_low_confidence_assessment(), _problems(), state=state)
    assert selected.difficulty <= _low_confidence_assessment().next_recommended_difficulty


def test_select_next_problem_treats_near_due_as_review_priority(monkeypatch):
    now = time.time()
    state = LearnerSkillState(
        skill_id="arrays",
        mastery_mu=45.0,
        mastery_variance=110.0,
        last_updated=now - 60,
        last_seen_timestamp=now - (86400 - 60 * 30),
        review_interval_seconds=86400.0,
        attempt_count=5,
        recent_attempts=[],
    )
    problem_states = {
        "near": ProblemState(
            problem_id="near",
            repetitions=2,
            ease_factor=2.5,
            interval_days=1.0,
            last_seen_timestamp=now - (86400 - 60 * 30),
        )
    }
    monkeypatch.setattr("src.engine.policy.random.random", lambda: 0.1)
    monkeypatch.setattr("src.engine.policy.random.choice", lambda seq: seq[0])

    selected = select_next_problem(
        _assessment(),
        _problems(),
        state=state,
        current_time=now,
        problem_states=problem_states,
    )
    assert selected.problem_id == "near"
