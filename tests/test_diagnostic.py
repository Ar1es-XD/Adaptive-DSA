from src.core.onboarding import DiagnosticTestResult, UserProfile, ProblemSolvingAbility, LearningPace
from src.core.diagnostic_test import (
    score_diagnostic_attempt,
    analyze_diagnostic_results,
    generate_custom_plan,
)

def test_score_diagnostic_attempt_perfect():
    result = score_diagnostic_attempt(
        "u1", "diag_1", "code", {"t1": True, "t2": True}, 90
    )
    assert result["correctness_score"] == 100.0
    assert result["efficiency_score"] == 100.0
    assert result["combined_score"] == 100.0

def test_score_diagnostic_attempt_partial_correct():
    result = score_diagnostic_attempt(
        "u1", "diag_1", "code", {"t1": True, "t2": False}, 90
    )
    assert result["correctness_score"] == 50.0
    assert result["efficiency_score"] == 100.0
    # 50 * 0.7 + 100 * 0.3 = 35 + 30 = 65
    assert result["combined_score"] == 65.0

def test_score_diagnostic_attempt_slow():
    # diag_1 limit is 180s. 360s -> efficiency 50%
    result = score_diagnostic_attempt(
        "u1", "diag_1", "code", {"t1": True, "t2": True}, 360
    )
    assert result["correctness_score"] == 100.0
    assert result["efficiency_score"] == 50.0
    # 100 * 0.7 + 50 * 0.3 = 70 + 15 = 85
    assert result["combined_score"] == 85.0

def test_analyze_diagnostic_results_foundational():
    profile = UserProfile(user_id="u1", email="x@x.com", name="x")
    test_res = DiagnosticTestResult(user_id="u1")
    # All scores very low
    test_res.scores = {"p1": 20, "p2": 30, "p3": 10, "p4": 0, "p5": 0}
    test_res.time_per_problem = {"p1": 100, "p2": 100, "p3": 300, "p4": 300, "p5": 300}
    
    am = analyze_diagnostic_results(test_res, profile)
    assert am.problem_solving_ability == ProblemSolvingAbility.FOUNDATIONAL
    assert am.learning_pace == LearningPace.SLOW

def test_analyze_diagnostic_results_advanced():
    profile = UserProfile(user_id="u2", email="y@y.com", name="y")
    test_res = DiagnosticTestResult(user_id="u2")
    test_res.scores = {"p1": 100, "p2": 100, "p3": 90, "p4": 90, "p5": 100}
    test_res.time_per_problem = {"p1": 50, "p2": 50, "p3": 100, "p4": 100, "p5": 100}
    
    am = analyze_diagnostic_results(test_res, profile)
    assert am.problem_solving_ability == ProblemSolvingAbility.ADVANCED
    assert am.learning_pace == LearningPace.FAST

def test_generate_custom_plan_foundational_slow():
    profile = UserProfile(user_id="u1", email="x@x.com", name="x")
    test_res = DiagnosticTestResult(user_id="u1")
    test_res.scores = {"p1": 20, "p2": 30, "p3": 10, "p4": 0, "p5": 0}
    test_res.time_per_problem = {"p1": 300, "p2": 300, "p3": 300, "p4": 300, "p5": 300}
    am = analyze_diagnostic_results(test_res, profile)
    plan = generate_custom_plan(am, profile)
    
    assert plan.daily_problem_count == 2
    assert plan.estimated_weeks == 20
    assert "arrays" in plan.phase_1_concepts

def test_generate_custom_plan_advanced_fast():
    profile = UserProfile(user_id="u1", email="x@x.com", name="x")
    test_res = DiagnosticTestResult(user_id="u1")
    test_res.scores = {"p1": 100, "p2": 100, "p3": 90, "p4": 90, "p5": 100}
    test_res.time_per_problem = {"p1": 50, "p2": 50, "p3": 100, "p4": 100, "p5": 100}
    am = analyze_diagnostic_results(test_res, profile)
    plan = generate_custom_plan(am, profile)
    
    assert plan.daily_problem_count == 4
    assert plan.estimated_weeks == 6
    assert "complex_graphs" in plan.phase_1_concepts
