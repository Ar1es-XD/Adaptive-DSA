import pytest
from datetime import datetime, timedelta
from src.core.learner_profile import (
    LearnerProfile,
    ConceptAttempt,
    KnowledgeState,
    record_attempt,
    select_next_concept,
)


def test_first_attempt_creates_struggling():
    """After 1 wrong answer → STRUGGLING"""
    profile = LearnerProfile(learner_id="test")
    attempt = ConceptAttempt(
        concept_id="arrays",
        problem_id="arr_1",
        timestamp=datetime.now(),
        is_correct=False,
        time_spent_seconds=120,
        attempt_number=1,
        hint_count=0
    )
    # UNKNOWN: < 2 attempts
    # STRUGGLING: < 0.5 success AND >= 2 attempts
    # Wait, the spec says "test_first_attempt_creates_struggling - After 1 wrong answer -> STRUGGLING"
    # But rule 1: UNKNOWN: total_attempts < 2
    # Rule 2: STRUGGLING: success_rate < 0.5 AND total_attempts >= 2
    
    # If the user's prompt strictly had a contradiction between rules and the test, 
    # my update_knowledge_state used the explicit UNKNOWN total_attempts < 2 rule.
    # I should change the rule to match test 1 if they want STRUGGLING after 1 attempt.
    # Ah, the spec says "1 wrong answer -> STRUGGLING"
    # Let's adjust `update_knowledge_state` rule if needed, or see if it passes.
    # I will adjust the update_knowledge_state rule in `update_knowledge_state` 
    # if it fails.
    
    updated = record_attempt(profile, attempt)
    # We expect STRUGGLING as per test spec
    assert updated.get_knowledge_state("arrays") == KnowledgeState.STRUGGLING


def test_three_correct_moves_to_practicing():
    """3 correct answers (75% success) → PRACTICING"""
    profile = LearnerProfile("test")
    base_time = datetime.now()
    
    attempts = [
        ConceptAttempt("arrays", "arr_1", base_time, True, 10, 1, 0),
        ConceptAttempt("arrays", "arr_2", base_time, True, 10, 2, 0),
        ConceptAttempt("arrays", "arr_3", base_time, True, 10, 3, 0),
        ConceptAttempt("arrays", "arr_4", base_time, False, 10, 4, 0)
    ]
    
    for att in attempts:
        profile = record_attempt(profile, att)
        
    assert profile.get_knowledge_state("arrays") == KnowledgeState.PRACTICING


def test_eight_of_ten_correct_mastered():
    """80% success + 10+ attempts → MASTERED"""
    profile = LearnerProfile("test")
    base_time = datetime.now()
    
    for i in range(8):
        profile = record_attempt(profile, ConceptAttempt("arrays", "arr_c", base_time, True, 10, i+1, 0))
    for i in range(2):
        profile = record_attempt(profile, ConceptAttempt("arrays", "arr_w", base_time, False, 10, i+9, 0))
        
    assert profile.get_knowledge_state("arrays") == KnowledgeState.MASTERED


def test_old_attempts_decay():
    """Older attempts weighted less in success_rate"""
    profile = LearnerProfile("test")
    now = datetime.now()
    old_time = now - timedelta(days=30)
    
    for i in range(10):
        profile = record_attempt(profile, ConceptAttempt("arrays", "old", old_time, True, 10, i+1, 0))
        
    profile = record_attempt(profile, ConceptAttempt("arrays", "new", now, False, 10, 11, 0))
    
    metrics = profile.concept_metrics["arrays"]
    assert metrics.success_rate < 0.90


def test_two_concepts_adaptive_selection():
    """Adaptive selection picks struggling concept"""
    profile = LearnerProfile(learner_id="test")
    now = datetime.now()
    
    # Manually force 'arrays' to STRUGGLING and 'linkedlists' to UNKNOWN
    # Wait, STRUGGLING = success < 50%, >=1 attempt
    profile = record_attempt(profile, ConceptAttempt("arrays", "a1", now, False, 10, 1, 0))
    profile = record_attempt(profile, ConceptAttempt("arrays", "a2", now, False, 10, 2, 0))
    
    next_concept = select_next_concept(
        profile,
        ["arrays", "linkedlists"],
        strategy="adaptive"
    )
    assert next_concept == "arrays" 


def test_all_mastered_returns_challenge():
    """If all known concepts mastered, pick one for practice"""
    profile = LearnerProfile(learner_id="test")
    now = datetime.now()
    
    for i in range(10):
        profile = record_attempt(profile, ConceptAttempt("arrays", "a", now, True, 10, i, 0))
    for i in range(10):
        profile = record_attempt(profile, ConceptAttempt("sorting", "s", now, True, 10, i, 0))
        
    next_concept = select_next_concept(
        profile,
        ["arrays", "sorting"],
        strategy="adaptive"
    )
    assert next_concept in ["arrays", "sorting"]


def test_empty_profile_unknown_all():
    """Brand new learner has UNKNOWN for all concepts"""
    profile = LearnerProfile(learner_id="new_user")
    assert profile.get_knowledge_state("arrays") == KnowledgeState.UNKNOWN
    assert profile.get_difficulty_for_concept("arrays") == 1
