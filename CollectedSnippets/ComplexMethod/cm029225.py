def _log_agent_event(self, max_steps: int, agent_run_error: str | None = None) -> None:
		"""Sent the agent event for this run to telemetry"""

		token_summary = self.token_cost_service.get_usage_tokens_for_model(self.llm.model)

		# Prepare action_history data correctly
		action_history_data = []
		for item in self.history.history:
			if item.model_output and item.model_output.action:
				# Convert each ActionModel in the step to its dictionary representation
				step_actions = [
					action.model_dump(exclude_unset=True)
					for action in item.model_output.action
					if action  # Ensure action is not None if list allows it
				]
				action_history_data.append(step_actions)
			else:
				# Append None or [] if a step had no actions or no model output
				action_history_data.append(None)

		final_res = self.history.final_result()
		final_result_str = json.dumps(final_res) if final_res is not None else None

		# Extract judgement data if available
		judgement_data = self.history.judgement()
		judge_verdict = judgement_data.get('verdict') if judgement_data else None
		judge_reasoning = judgement_data.get('reasoning') if judgement_data else None
		judge_failure_reason = judgement_data.get('failure_reason') if judgement_data else None
		judge_reached_captcha = judgement_data.get('reached_captcha') if judgement_data else None
		judge_impossible_task = judgement_data.get('impossible_task') if judgement_data else None

		self.telemetry.capture(
			AgentTelemetryEvent(
				task=self.task,
				model=self.llm.model,
				model_provider=self.llm.provider,
				max_steps=max_steps,
				max_actions_per_step=self.settings.max_actions_per_step,
				use_vision=self.settings.use_vision,
				version=self.version,
				source=self.source,
				cdp_url=urlparse(self.browser_session.cdp_url).hostname
				if self.browser_session and self.browser_session.cdp_url
				else None,
				agent_type=None,  # Regular Agent (not code-use)
				action_errors=self.history.errors(),
				action_history=action_history_data,
				urls_visited=self.history.urls(),
				steps=self.state.n_steps,
				total_input_tokens=token_summary.prompt_tokens,
				total_output_tokens=token_summary.completion_tokens,
				prompt_cached_tokens=token_summary.prompt_cached_tokens,
				total_tokens=token_summary.total_tokens,
				total_duration_seconds=self.history.total_duration_seconds(),
				success=self.history.is_successful(),
				final_result_response=final_result_str,
				error_message=agent_run_error,
				judge_verdict=judge_verdict,
				judge_reasoning=judge_reasoning,
				judge_failure_reason=judge_failure_reason,
				judge_reached_captcha=judge_reached_captcha,
				judge_impossible_task=judge_impossible_task,
			)
		)