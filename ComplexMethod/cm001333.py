def _process_reflection(
        self, response_dict: dict[str, Any], verbal_text: Optional[str] = None
    ) -> None:
        """Process a reflection response and store in memory.

        Args:
            response_dict: Parsed JSON response (for structured reflections)
            verbal_text: Raw verbal reflection text (for verbal format)
        """
        reflection_format = self._get_reflection_format()

        if reflection_format == "verbal" and verbal_text:
            # Verbal reflection format (from Reflexion paper)
            # Extract evaluation score if available
            evaluation_score = (
                self.last_evaluation.score if self.last_evaluation else None
            )
            success = self.last_evaluation.success if self.last_evaluation else True

            reflection = Reflection(
                action_name=(
                    self.last_action.get("name", "unknown")
                    if self.last_action
                    else "unknown"
                ),
                action_arguments=(
                    self.last_action.get("arguments", {}) if self.last_action else {}
                ),
                result_summary=self.last_result or "",
                verbal_reflection=verbal_text,
                reflection_format="verbal",
                evaluation_score=evaluation_score,
                success=success,
                timestamp=datetime.now(),
            )

            self.memory.add_reflection(reflection)
            self.logger.debug(
                f"Stored verbal reflection: {reflection.to_prompt_text()}"
            )

            # Handle retry logic based on evaluation
            if not success and self.retry_count < self.config.max_retry_attempts:
                self.retry_count += 1
                self.logger.info(
                    f"Evaluation suggests retry (attempt {self.retry_count})"
                )
            else:
                self.retry_count = 0
            return

        # Structured reflection format (original behavior)
        action_summary = response_dict.get("action_summary", "")
        result_analysis = response_dict.get("result_analysis", "")
        what_failed = response_dict.get("what_failed", "")
        lesson_learned = response_dict.get("lesson_learned", "")
        # root_cause is extracted but not used in the current implementation
        # It could be added to the Reflection model in the future
        _ = response_dict.get("root_cause", "")
        should_retry = response_dict.get("should_retry", False)

        # Determine success
        success = not what_failed or what_failed.lower() in (
            "",
            "nothing",
            "none",
            "n/a",
        )

        # Include evaluation score if available
        evaluation_score = self.last_evaluation.score if self.last_evaluation else None

        # Create and store reflection
        reflection = Reflection(
            action_name=(
                self.last_action.get("name", "unknown")
                if self.last_action
                else "unknown"
            ),
            action_arguments=(
                self.last_action.get("arguments", {}) if self.last_action else {}
            ),
            result_summary=result_analysis or action_summary,
            what_went_wrong=what_failed if not success else "",
            what_to_do_differently=lesson_learned,
            success=success,
            evaluation_score=evaluation_score,
            timestamp=datetime.now(),
        )

        self.memory.add_reflection(reflection)
        self.logger.debug(f"Stored reflection: {reflection.to_prompt_text()}")

        # Handle retry logic
        if should_retry and self.retry_count < self.config.max_retry_attempts:
            self.retry_count += 1
            self.logger.info(f"Reflection suggests retry (attempt {self.retry_count})")
        else:
            self.retry_count = 0