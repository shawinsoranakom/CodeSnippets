def evaluate(
        self, result: ChallengeResult, challenge: Challenge
    ) -> ChallengeResult:
        """Evaluate a challenge result and update success/score.

        For timed-out challenges, we still run evaluation to populate the score
        (so we can show "would have passed"), but success remains False.
        """
        ground = challenge.ground_truth

        if not ground:
            # No ground truth defined, can't evaluate
            result.success = False
            result.score = 0.0
            result.error_message = (
                result.error_message or "No ground truth defined for evaluation"
            )
            return result

        # Get evaluation type
        eval_config = ground.get("eval", {})
        eval_type = eval_config.get("type", "file")

        # Get target files
        target_files = ground.get("files", [])

        # Collect content from output files
        content = self._collect_eval_content(result, target_files)

        # Run evaluation based on type
        try:
            if eval_type == "python":
                score = self._eval_python(result, challenge, target_files)
            elif eval_type == "pytest":
                score = self._eval_pytest(result, challenge)
            elif eval_type == "llm":
                # LLM evaluation not yet implemented, fall back to string match
                score = self._eval_string_match(content, ground)
            else:
                # Default: string matching (type "file" or unspecified)
                score = self._eval_string_match(content, ground)
        except Exception as e:
            score = 0.0
            result.error_message = f"Evaluation error: {e}"

        # Update result
        result.score = score
        # Timed-out challenges cannot pass, even if evaluation would succeed
        # (The score is still set so UI can show "would have passed")
        if result.timed_out:
            result.success = False
        else:
            result.success = score >= 0.9  # 90% threshold for success

        return result