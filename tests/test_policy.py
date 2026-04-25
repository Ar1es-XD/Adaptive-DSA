import time

from src.engine.policy import select_next_problem
from src.models.learner import LearnerSkillState, Problem, SkillAssessment


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
        last_seen_timestamp=now - (86400 * 2),
        review_interval_seconds=86400.0,
        attempt_count=5,
        recent_attempts=[],
    )
    monkeypatch.setattr("src.engine.policy.random.choice", lambda seq: seq[0])

    selected = select_next_problem(_assessment(), _problems(), state=state, current_time=now)
    assert selected.difficulty <= _assessment().next_recommended_difficulty
