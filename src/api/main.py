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
from src.core.diagnostic_test import score_diagnostic_attempt, analyze_diagnostic_results, generate_custom_plan
from typing import Dict
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

# --- ONBOARDING ENDPOINTS ---

# In-memory stores for onboarding state
_users = {}
_diagnostics = {}
_ability_maps = {}
_plans = {}

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
    _users[user_id] = profile
    _diagnostics[user_id] = DiagnosticTestResult(user_id=user_id)
    return {"user_id": user_id, "userProfile": profile, "auth_token": "mock_token"}

class DiagnosticSubmitRequest(BaseModel):
    user_id: str
    problem_id: str
    submitted_code: str
    execution_results: Dict[str, bool]
    time_spent_seconds: int

@app.post("/api/diagnostic/submit-attempt")
def diagnostic_submit(req: DiagnosticSubmitRequest):
    result = score_diagnostic_attempt(
        req.user_id, 
        req.problem_id, 
        req.submitted_code, 
        req.execution_results, 
        req.time_spent_seconds
    )
    
    # Save into memory
    diag = _diagnostics.get(req.user_id)
    if diag:
        diag.scores[req.problem_id] = result["combined_score"]
        diag.time_per_problem[req.problem_id] = req.time_spent_seconds
        
    return {"score": result["combined_score"], "feedback": result}

class DiagnosticFinalizeRequest(BaseModel):
    user_id: str
    all_problem_ids: list[str]

@app.post("/api/diagnostic/finalize")
def diagnostic_finalize(req: DiagnosticFinalizeRequest):
    diag = _diagnostics.get(req.user_id)
    profile = _users.get(req.user_id)
    ability_map = analyze_diagnostic_results(diag, profile)
    _ability_maps[req.user_id] = ability_map
    return {"abilityMap": ability_map, "confidence_score": ability_map.confidence_score}

class PlanGenerateRequest(BaseModel):
    user_id: str

@app.post("/api/learning-plan/generate")
def learning_plan_generate(req: PlanGenerateRequest):
    profile = _users.get(req.user_id)
    ability_map = _ability_maps.get(req.user_id)
    plan = generate_custom_plan(ability_map, profile)
    _plans[req.user_id] = plan
    return {"learningPlan": plan}

class DashboardInitRequest(BaseModel):
    user_id: str

@app.post("/api/dashboard/initialize")
def dashboard_initialize(req: DashboardInitRequest):
    # Return learner state and first problem from plan
    plan = _plans.get(req.user_id)
    # mock problem extraction
    first_target_concept = plan.phase_1_concepts[0] if plan.phase_1_concepts else "arrays"
    # Call service state
    return {"first_problem": first_target_concept, "learner_profile_state": {}}
