def _log_step_completion_summary(self, step_start_time: float, result: list[ActionResult]) -> str | None:
		"""Log step completion summary with action count, timing, and success/failure stats"""
		if not result:
			return None

		step_duration = time.time() - step_start_time
		action_count = len(result)

		# Count success and failures
		success_count = sum(1 for r in result if not r.error)
		failure_count = action_count - success_count

		# Format success/failure indicators
		success_indicator = f'✅ {success_count}' if success_count > 0 else ''
		failure_indicator = f'❌ {failure_count}' if failure_count > 0 else ''
		status_parts = [part for part in [success_indicator, failure_indicator] if part]
		status_str = ' | '.join(status_parts) if status_parts else '✅ 0'

		message = (
			f'📍 Step {self.state.n_steps}: Ran {action_count} action{"" if action_count == 1 else "s"} '
			f'in {step_duration:.2f}s: {status_str}'
		)
		self.logger.debug(message)
		return message