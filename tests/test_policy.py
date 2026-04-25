from src.engine.policy import select_next_problem
from src.models.learner import Problem, SkillAssessment


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
