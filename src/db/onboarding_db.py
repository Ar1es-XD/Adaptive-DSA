import sqlite3
import json
from datetime import datetime
from src.core.onboarding import UserProfile, DiagnosticTestResult, AbilityMap, CustomLearningPlan, ProblemSolvingAbility, LearningPace

DB_PATH = "learner.db"

def init_onboarding_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                email TEXT,
                name TEXT,
                years_coding INTEGER,
                dsa_experience TEXT,
                created_at TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS diagnostic_results (
                user_id TEXT PRIMARY KEY,
                scores TEXT,
                time_per_problem TEXT,
                total_score REAL,
                efficiency_score REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ability_maps (
                user_id TEXT PRIMARY KEY,
                problem_solving_ability INTEGER,
                learning_pace INTEGER,
                confidence_score REAL,
                time_complexity_grasp REAL,
                code_correctness REAL,
                logical_thinking REAL,
                optimization_tendency REAL,
                strengths TEXT,
                gaps TEXT,
                created_at TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_plans (
                user_id TEXT PRIMARY KEY,
                ability_level INTEGER,
                phase_1_concepts TEXT,
                phase_2_concepts TEXT,
                phase_3_concepts TEXT,
                daily_problem_count INTEGER,
                estimated_weeks INTEGER,
                focus_areas TEXT,
                milestone_problems TEXT,
                created_at TEXT
            )
        ''')
        conn.commit()

init_onboarding_db()

def save_user_profile(user: UserProfile):
    with sqlite3.connect(DB_PATH) as conn:
        conn.cursor().execute('''
            INSERT OR REPLACE INTO user_profiles VALUES (?, ?, ?, ?, ?, ?)
        ''', (user.user_id, user.email, user.name, user.years_coding, user.dsa_experience, user.created_at.isoformat()))
        conn.commit()

def get_user_profile(user_id: str) -> UserProfile:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.cursor().execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,)).fetchone()
        if row:
            return UserProfile(row[0], row[1], row[2], datetime.fromisoformat(row[5]), row[3], row[4])
    return None

def save_diagnostic_result(result: DiagnosticTestResult):
    with sqlite3.connect(DB_PATH) as conn:
        conn.cursor().execute('''
            INSERT OR REPLACE INTO diagnostic_results VALUES (?, ?, ?, ?, ?)
        ''', (result.user_id, json.dumps(result.scores), json.dumps(result.time_per_problem), result.total_score, result.efficiency_score))
        conn.commit()

def get_diagnostic_result(user_id: str) -> DiagnosticTestResult:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.cursor().execute('SELECT * FROM diagnostic_results WHERE user_id = ?', (user_id,)).fetchone()
        if row:
            res = DiagnosticTestResult(user_id=row[0])
            res.scores = json.loads(row[1])
            res.time_per_problem = json.loads(row[2])
            res.total_score = row[3]
            res.efficiency_score = row[4]
            return res
    return None

def save_ability_map(am: AbilityMap):
    with sqlite3.connect(DB_PATH) as conn:
        conn.cursor().execute('''
            INSERT OR REPLACE INTO ability_maps VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (am.user_id, am.problem_solving_ability.value, am.learning_pace.value, am.confidence_score,
              am.time_complexity_grasp, am.code_correctness, am.logical_thinking, am.optimization_tendency,
              json.dumps(am.strengths), json.dumps(am.gaps), am.created_at.isoformat()))
        conn.commit()

def get_ability_map(user_id: str) -> AbilityMap:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.cursor().execute('SELECT * FROM ability_maps WHERE user_id = ?', (user_id,)).fetchone()
        if row:
            return AbilityMap(
                user_id=row[0], problem_solving_ability=ProblemSolvingAbility(row[1]),
                learning_pace=LearningPace(row[2]), confidence_score=row[3],
                time_complexity_grasp=row[4], code_correctness=row[5], logical_thinking=row[6],
                optimization_tendency=row[7], strengths=json.loads(row[8]), gaps=json.loads(row[9]),
                created_at=datetime.fromisoformat(row[10])
            )
    return None

def save_learning_plan(plan: CustomLearningPlan):
    with sqlite3.connect(DB_PATH) as conn:
        conn.cursor().execute('''
            INSERT OR REPLACE INTO learning_plans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (plan.user_id, plan.ability_level.value, json.dumps(plan.phase_1_concepts),
              json.dumps(plan.phase_2_concepts), json.dumps(plan.phase_3_concepts),
              plan.daily_problem_count, plan.estimated_weeks, json.dumps(plan.focus_areas),
              json.dumps(plan.milestone_problems), plan.created_at.isoformat()))
        conn.commit()

def get_learning_plan(user_id: str) -> CustomLearningPlan:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.cursor().execute('SELECT * FROM learning_plans WHERE user_id = ?', (user_id,)).fetchone()
        if row:
            return CustomLearningPlan(
                user_id=row[0], ability_level=ProblemSolvingAbility(row[1]),
                phase_1_concepts=json.loads(row[2]), phase_2_concepts=json.loads(row[3]), phase_3_concepts=json.loads(row[4]),
                daily_problem_count=row[5], estimated_weeks=row[6], focus_areas=json.loads(row[7]),
                milestone_problems=json.loads(row[8]), created_at=datetime.fromisoformat(row[9])
            )
    return None
