from src.engine.learner_model import assess_mastery, initialize_skill_state


def test_initialize_skill_state_defaults():
    state = initialize_skill_state("arrays")
    assert state.skill_id == "arrays"
    assert state.mastery_mu == 50.0
    assert state.mastery_variance == 225.0
    assert state.attempt_count == 0


def test_assess_mastery_shape():
    state = initialize_skill_state("dp")
    assessment = assess_mastery(state)
    assert assessment.skill_id == "dp"
    assert 0 <= assessment.confidence <= 100
    assert 1 <= assessment.next_recommended_difficulty <= 10
