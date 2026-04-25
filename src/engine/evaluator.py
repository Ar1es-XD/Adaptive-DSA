from src.models.learner import Problem


class ProblemEvaluator:
    """Evaluates user solution correctness."""

    @staticmethod
    def _normalize_answer(answer: str) -> str:
        return answer.strip().lower()

    def check_solution(self, problem: Problem, user_answer: str) -> bool:
        """Return True only when normalized answer matches expected output."""
        normalized_user = self._normalize_answer(user_answer)
        normalized_expected = self._normalize_answer(problem.expected_output)
        return normalized_user == normalized_expected

    def get_hint(self, problem: Problem, incorrect_attempts: int) -> str:
        """Return hint 1 on first failure and hint 2 on second+ failure."""
        if not problem.hints:
            return self.get_explanation(problem)
        if incorrect_attempts <= 1:
            return problem.hints[0]
        if len(problem.hints) > 1:
            return problem.hints[1]
        return problem.hints[0]

    def get_explanation(self, problem: Problem) -> str:
        """Return hint/explanation."""
        return f"Hint for {problem.title}: Use a {problem.pattern} approach"
