from src.models.learner import Problem


class ProblemEvaluator:
    """Evaluates user solution correctness."""

    @staticmethod
    def _normalize_answer(answer: str) -> str:
        return " ".join(answer.strip().lower().split())

    def check_solution(self, problem: Problem, user_answer: str) -> bool:
        """Return True only when normalized answer matches expected output."""
        normalized_user = self._normalize_answer(user_answer)
        normalized_expected = self._normalize_answer(problem.expected_output)
        return normalized_user == normalized_expected

    def get_hint(self, problem: Problem, incorrect_attempts: int) -> str:
        """Return hint 1 on first failure and hint 2 on second+ failure."""
        if problem.hints:
            idx = max(0, incorrect_attempts - 1)
            return problem.hints[min(idx, len(problem.hints) - 1)]
        return "No hints available"

    def get_explanation(self, problem: Problem) -> str:
        """Return hint/explanation."""
        return f"Hint for {problem.title}: Use a {problem.pattern} approach"
