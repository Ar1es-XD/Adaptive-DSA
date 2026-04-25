from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict
from enum import Enum

class ProblemSolvingAbility(Enum):
    """Learner's demonstrated problem-solving level"""
    FOUNDATIONAL = 1      # Struggles with logic, needs guidance
    EMERGING = 2          # Understands basics, inconsistent
    DEVELOPING = 3        # Solid grasp, can solve most
    PROFICIENT = 4        # Strong problem solver, quick thinking
    ADVANCED = 5          # Expert-level, optimizes solutions

class LearningPace(Enum):
    """How fast they should progress"""
    SLOW = 1              # More time per concept, more examples
    MODERATE = 2          # Standard pace
    FAST = 3              # Accelerated, challenge problems

@dataclass
class UserProfile:
    """User signup info"""
    user_id: str
    email: str
    name: str
    created_at: datetime = field(default_factory=datetime.now)
    years_coding: int = 0  # 0-1, 1-3, 3-5, 5+
    dsa_experience: str = "none"  # none, little, some, experienced
    
    def get_background_level(self) -> int:
        """Map experience to 1-5 scale"""
        exp_map = {"none": 1, "little": 2, "some": 3, "experienced": 4}
        return exp_map.get(self.dsa_experience, 1)

@dataclass
class DiagnosticTestResult:
    """Raw test performance"""
    user_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    scores: Dict[str, int] = field(default_factory=dict)
    time_per_problem: Dict[str, int] = field(default_factory=dict)
    
    total_score: float = 0.0  # weighted average
    efficiency_score: float = 0.0  # speed + accuracy combined

@dataclass
class AbilityMap:
    """Learner's assessed capability"""
    user_id: str
    problem_solving_ability: ProblemSolvingAbility
    learning_pace: LearningPace
    confidence_score: float  # 0.0-1.0, how confident are we
    
    # Detailed breakdown
    time_complexity_grasp: float  # 0.0-1.0
    code_correctness: float  # 0.0-1.0
    logical_thinking: float  # 0.0-1.0
    optimization_tendency: float  # 0.0-1.0
    
    # Why these specific areas
    strengths: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class CustomLearningPlan:
    """Tailored DSA roadmap"""
    user_id: str
    ability_level: ProblemSolvingAbility
    
    # Structured progression
    phase_1_concepts: List[str]  # Foundation (Arrays, Strings, etc)
    phase_2_concepts: List[str]  # Core (Stacks, Queues, Trees)
    phase_3_concepts: List[str]  # Advanced (Graphs, DP, Greedy)
    
    # Customization
    daily_problem_count: int  # 2-5 based on pace
    estimated_weeks: int
    focus_areas: List[str]  # e.g., ["time-complexity", "recursion"]
    
    # Milestones
    milestone_problems: Dict[str, str]  # {concept: checkpoint_problem_id}
    
    created_at: datetime = field(default_factory=datetime.now)
