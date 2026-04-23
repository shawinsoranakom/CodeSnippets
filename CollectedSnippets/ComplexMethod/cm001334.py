def record_result(self, result: str, success: Optional[bool] = None) -> None:
        """Record the result of an action and trigger reflection if needed.

        Args:
            result: The result string from executing the action
            success: Override for success determination. If None, uses evaluator.
        """
        self.last_result = result

        # Run evaluator if success is not explicitly provided
        if success is None:
            if self.config.evaluator_type == EvaluatorType.HEURISTIC:
                self.last_evaluation = self._evaluate_heuristic(result)
                success = self.last_evaluation.success
            else:
                # For LLM evaluator, would need to make an LLM call
                # For now, fall back to heuristic
                self.last_evaluation = self._evaluate_heuristic(result)
                success = self.last_evaluation.success
        else:
            # Create evaluation result from explicit success
            self.last_evaluation = EvaluationResult(
                success=success,
                score=0.9 if success else 0.1,
                feedback="Explicit success/failure provided",
            )

        if self.config.always_reflect or not success:
            if success and not self.config.reflect_on_success:
                # Skip reflection for successful actions if configured
                return
            self.current_phase = ReflexionPhase.REFLECTING