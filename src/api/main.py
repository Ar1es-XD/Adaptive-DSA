from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.services.tutor_service import (
    get_analytics_summary,
    get_recommend,
    get_review,
    get_status,
    start_problem,
    start_session,
    submit_answer,
)

from src.core.onboarding import UserProfile, DiagnosticTestResult, AbilityMap, CustomLearningPlan
from src.core.diagnostic_test import (
    score_diagnostic_attempt, 
    analyze_diagnostic_results, 
    generate_custom_plan,
    DIAGNOSTIC_PROBLEMS
)
from src.db.onboarding_db import (
    save_user_profile,
    get_user_profile,
    save_diagnostic_result,
    get_diagnostic_result,
    save_ability_map,
    get_ability_map,
    save_learning_plan,
    get_learning_plan
)
from src.core.sandbox import run_tests_on_code
from fastapi.encoders import jsonable_encoder
from typing import Dict, Optional
import uuid


class StartPracticeRequest(BaseModel):
    topic: str


class SubmitPracticeRequest(BaseModel):
    problem_id: str
    answer: str


class PracticeProblemRequest(BaseModel):
    problem_id: str


app = FastAPI(title="Adaptive DSA Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/practice/start")
def practice_start(req: StartPracticeRequest):
    return start_session(req.topic)


@app.post("/practice/submit")
def practice_submit(req: SubmitPracticeRequest):
    return submit_answer(req.problem_id, req.answer)


@app.post("/practice/problem")
def practice_problem(req: PracticeProblemRequest):
    return start_problem(req.problem_id)


@app.get("/status/{topic}")
def status(topic: str):
    return get_status(topic)


@app.get("/review")
def review():
    return get_review()


@app.get("/recommend")
def recommend():
    return get_recommend()


@app.get("/analytics/summary")
def analytics_summary():
    return get_analytics_summary()

# Onboarding State operates on SQLite via onboarding_db.py

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str
    years_coding: int
    dsa_experience: str

@app.post("/api/auth/signup")
def signup(req: SignupRequest):
    user_id = str(uuid.uuid4())
    profile = UserProfile(
        user_id=user_id,
        email=req.email,
        name=req.name,
        years_coding=req.years_coding,
        dsa_experience=req.dsa_experience
    )
    save_user_profile(profile)
    save_diagnostic_result(DiagnosticTestResult(user_id=user_id))
    return jsonable_encoder({"user_id": user_id, "userProfile": profile, "auth_token": "mock_token"})

class DiagnosticSubmitRequest(BaseModel):
    user_id: str
    problem_id: str
    submitted_code: str
    time_spent_seconds: int

@app.post("/api/diagnostic/submit-attempt")
def diagnostic_submit(req: DiagnosticSubmitRequest):
    # Lookup problem tests
    prob_def = next((p for p in DIAGNOSTIC_PROBLEMS if p["id"] == req.problem_id), None)
    if not prob_def:
        return {"error": "Invalid problem ID"}
        
    # Execute actual code
    test_cases = prob_def.get("test_cases", [])
    execution_results = run_tests_on_code(req.submitted_code, test_cases)
    
    result = score_diagnostic_attempt(
        req.user_id, 
        req.problem_id, 
        req.submitted_code, 
        execution_results, 
        req.time_spent_seconds
    )
    
    # Save into SQLite
    diag = get_diagnostic_result(req.user_id)
    if diag:
        diag.scores[req.problem_id] = result["combined_score"]
        diag.time_per_problem[req.problem_id] = req.time_spent_seconds
        save_diagnostic_result(diag)
        
    return jsonable_encoder({"score": result["combined_score"], "feedback": result, "execution_results": execution_results})

class DiagnosticFinalizeRequest(BaseModel):
    user_id: str
    all_problem_ids: list[str]

@app.post("/api/diagnostic/finalize")
def diagnostic_finalize(req: DiagnosticFinalizeRequest):
    diag = get_diagnostic_result(req.user_id)
    profile = get_user_profile(req.user_id)
    ability_map = analyze_diagnostic_results(diag, profile)
    save_ability_map(ability_map)
    return jsonable_encoder({"abilityMap": ability_map, "confidence_score": ability_map.confidence_score})

class PlanGenerateRequest(BaseModel):
    user_id: str

@app.post("/api/learning-plan/generate")
def learning_plan_generate(req: PlanGenerateRequest):
    profile = get_user_profile(req.user_id)
    ability_map = get_ability_map(req.user_id)
    plan = generate_custom_plan(ability_map, profile)
    save_learning_plan(plan)
    return jsonable_encoder({"learningPlan": plan})

class DashboardInitRequest(BaseModel):
    user_id: str

@app.post("/api/dashboard/initialize")
def dashboard_initialize(req: DashboardInitRequest):
    # Return learner state and first problem from plan
    plan = get_learning_plan(req.user_id)
    if not plan:
        return {"error": "Plan not found"}
    # mock problem extraction
    first_target_concept = plan.phase_1_concepts[0] if plan.phase_1_concepts else "arrays"
    # Call service state
    return jsonable_encoder({"first_problem": first_target_concept, "learner_profile_state": {}})
