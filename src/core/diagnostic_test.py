from typing import List, Dict, Any
from datetime import datetime
from src.core.onboarding import DiagnosticTestResult, AbilityMap, ProblemSolvingAbility, LearningPace, UserProfile, CustomLearningPlan

DIAGNOSTIC_PROBLEMS = [
    {
        "id": "diag_1",
        "title": "Two Sum",
        "difficulty": 1,
        "category": "arrays",
        "time_limit_seconds": 180,
    },
    {
        "id": "diag_2",
        "title": "Reverse String",
        "difficulty": 1,
        "category": "strings",
        "time_limit_seconds": 120,
    },
    {
        "id": "diag_3",
        "title": "Binary Tree Level Order Traversal",
        "difficulty": 3,
        "category": "trees",
        "time_limit_seconds": 300,
    },
    {
        "id": "diag_4",
        "title": "Longest Substring Without Repeating",
        "difficulty": 3,
        "category": "strings",
        "time_limit_seconds": 300,
    },
    {
        "id": "diag_5",
        "title": "Median of Two Sorted Arrays",
        "difficulty": 5,
        "category": "arrays",
        "time_limit_seconds": 600,
    },
]

def score_diagnostic_attempt(
    user_id: str,
    problem_id: str,
    submitted_code: str,
    execution_results: Dict[str, bool],
    time_spent_seconds: int
) -> Dict[str, Any]:
    """Score a single diagnostic problem."""
    # Find problem limits
    problem_def = next((p for p in DIAGNOSTIC_PROBLEMS if p["id"] == problem_id), None)
    if not problem_def:
        raise ValueError(f"Unknown diagnostic problem {problem_id}")
        
    time_limit = problem_def["time_limit_seconds"]
    
    if not execution_results:
        correctness = 0.0
    else:
        passed = sum(1 for passed in execution_results.values() if passed)
        correctness = (passed / len(execution_results)) * 100.0
        
    # Efficiency calculation
    if time_spent_seconds <= 0:
        efficiency = 100.0
    else:
        efficiency = min(100.0, (time_limit / time_spent_seconds) * 100.0)
        
    combined = (correctness * 0.7) + (efficiency * 0.3)
    
    return {
        "problem_id": problem_id,
        "correctness_score": round(correctness, 2),
        "efficiency_score": round(efficiency, 2),
        "combined_score": round(combined, 2)
    }

def analyze_diagnostic_results(
    test_result: DiagnosticTestResult,
    user_profile: 'UserProfile'
) -> AbilityMap:
    """Convert test scores → ability assessment."""
    if not test_result.scores:
        return AbilityMap(
            user_id=test_result.user_id,
            problem_solving_ability=ProblemSolvingAbility.FOUNDATIONAL,
            learning_pace=LearningPace.SLOW,
            confidence_score=0.1,
            time_complexity_grasp=0.0,
            code_correctness=0.0,
            logical_thinking=0.0,
            optimization_tendency=0.0,
            strengths=[],
            gaps=["Needs absolute fundamentals."]
        )

    # Convert scores out of 100 to overall average
    scores = list(test_result.scores.values())
    avg_score = sum(scores) / len(scores)
    
    times = list(test_result.time_per_problem.values())
    avg_time = sum(times) / len(times) if times else 300

    if avg_score < 50:
        ability = ProblemSolvingAbility.FOUNDATIONAL
        pace = LearningPace.SLOW
    elif avg_score < 65:
        ability = ProblemSolvingAbility.EMERGING
        pace = LearningPace.MODERATE if avg_time < 200 else LearningPace.SLOW
    elif avg_score < 80:
        ability = ProblemSolvingAbility.DEVELOPING
        pace = LearningPace.MODERATE
    elif avg_score < 90:
        ability = ProblemSolvingAbility.PROFICIENT
        pace = LearningPace.FAST if avg_time < 150 else LearningPace.MODERATE
    else:
        ability = ProblemSolvingAbility.ADVANCED
        pace = LearningPace.FAST

    strengths = []
    gaps = []
    
    # Simple heuristics
    if avg_score > 70:
        strengths.append("Consistent logical thinking")
    else:
        gaps.append("Needs stronger foundational logic")
        
    if avg_time > 250:
        gaps.append("Speed and confidence could improve")
    else:
        strengths.append("Fast problem solver")

    return AbilityMap(
        user_id=test_result.user_id,
        problem_solving_ability=ability,
        learning_pace=pace,
        confidence_score=0.85,
        time_complexity_grasp=avg_score / 100.0,
        code_correctness=avg_score / 100.0,
        logical_thinking=avg_score / 100.0,
        optimization_tendency=(avg_score / 100.0) * 0.8,
        strengths=strengths,
        gaps=gaps
    )

def generate_custom_plan(
    ability_map: AbilityMap,
    user_profile: 'UserProfile'
) -> 'CustomLearningPlan':
    """Create personalized DSA learning path."""
    ability = ability_map.problem_solving_ability
    pace = ability_map.learning_pace
    
    if ability == ProblemSolvingAbility.FOUNDATIONAL:
        p1 = ["arrays", "strings", "basic_recursion"]
        p2 = ["stacks", "queues", "linked_lists"]
        p3 = ["trees", "basic_sorting"]
    elif ability == ProblemSolvingAbility.EMERGING:
        p1 = ["arrays", "strings", "linked_lists"]
        p2 = ["trees", "stacks", "hash_tables"]
        p3 = ["graphs", "dp_intro"]
    elif ability == ProblemSolvingAbility.DEVELOPING:
        p1 = ["linked_lists", "trees", "sorting"]
        p2 = ["graphs", "hash_tables", "binary_search"]
        p3 = ["dp", "greedy"]
    elif ability == ProblemSolvingAbility.PROFICIENT:
        p1 = ["trees", "sorting", "binary_search"]
        p2 = ["graphs", "dp", "backtracking"]
        p3 = ["segment_trees", "tries"]
    else:
        p1 = ["complex_graphs", "advanced_dp"]
        p2 = ["optimization", "system_design_prep"]
        p3 = ["competitive_programming_patterns"]

    daily = 3
    weeks = 12
    if ability == ProblemSolvingAbility.FOUNDATIONAL:
        if pace == LearningPace.SLOW:
            daily, weeks = 2, 20
        else:
            daily, weeks = 3, 14
    elif ability == ProblemSolvingAbility.EMERGING:
        daily, weeks = 4, 12
    elif ability == ProblemSolvingAbility.PROFICIENT:
        daily, weeks = 5, 8
    elif ability == ProblemSolvingAbility.ADVANCED:
        daily, weeks = 4, 6

    focus = ["optimization"] if "Speed and confidence could improve" in ability_map.gaps else ["advanced-patterns"]

    return CustomLearningPlan(
        user_id=user_profile.user_id,
        ability_level=ability,
        phase_1_concepts=p1,
        phase_2_concepts=p2,
        phase_3_concepts=p3,
        daily_problem_count=daily,
        estimated_weeks=weeks,
        focus_areas=focus,
        milestone_problems={}
    )
