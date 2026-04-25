from src.engine.evaluator import ProblemEvaluator
from src.models.learner import Problem


def _make_problem(hints=None):
    return Problem(
        problem_id="p1",
        title="Sample",
        description="desc",
        topic="arrays",
        difficulty=3,
        pattern="twoPointer",
        expected_output="indices 0 and 1",
        hints=hints if hints is not None else ["hint one", "hint two"],
    )


def test_check_solution_normalizes_whitespace_and_case():
    evaluator = ProblemEvaluator()
    problem = _make_problem()
    assert evaluator.check_solution(problem, "  INDICES   0   AND   1  ")


def test_get_hint_progression_and_safe_fallback():
    evaluator = ProblemEvaluator()
    problem = _make_problem(["h1", "h2"])
    assert evaluator.get_hint(problem, 1) == "h1"
    assert evaluator.get_hint(problem, 2) == "h2"
    assert evaluator.get_hint(problem, 5) == "h2"

    no_hint_problem = _make_problem([])
    assert evaluator.get_hint(no_hint_problem, 1) == "No hints available"
