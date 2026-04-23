def _evaluate_heuristic(self, result: str) -> EvaluationResult:
        """Simple heuristic evaluation based on error patterns.

        This is the default evaluator that looks for common error indicators
        in the result string. For more sophisticated evaluation, use
        evaluator_type=EvaluatorType.LLM.
        """
        error_patterns = [
            "error",
            "failed",
            "exception",
            "traceback",
            "invalid",
            "not found",
            "permission denied",
            "timeout",
            "refused",
            "cannot",
            "unable to",
        ]

        result_lower = result.lower()
        has_error = any(pattern in result_lower for pattern in error_patterns)

        # Check for success patterns that might override error detection
        success_patterns = [
            "success",
            "completed",
            "done",
            "finished",
            "created",
            "saved",
        ]
        has_success = any(pattern in result_lower for pattern in success_patterns)

        # If both error and success patterns, look at which appears first
        if has_error and has_success:
            # Find first occurrence of each
            first_error_idx = min(
                (result_lower.find(p) for p in error_patterns if p in result_lower),
                default=len(result_lower),
            )
            first_success_idx = min(
                (result_lower.find(p) for p in success_patterns if p in result_lower),
                default=len(result_lower),
            )
            has_error = first_error_idx < first_success_idx

        if has_error:
            return EvaluationResult(
                success=False,
                score=0.2,
                feedback="Detected error patterns in output",
            )
        else:
            return EvaluationResult(
                success=True,
                score=0.8,
                feedback="Execution completed without detected errors",
            )