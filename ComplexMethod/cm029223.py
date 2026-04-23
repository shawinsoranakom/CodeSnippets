async def _broadcast_model_state(self, parsed: 'AgentOutput') -> None:
		if not self._demo_mode_enabled:
			return

		state = parsed.current_state
		step_meta = {'step': self.state.n_steps}

		if state.thinking:
			await self._demo_mode_log(state.thinking, 'thought', step_meta)

		if state.evaluation_previous_goal:
			eval_text = state.evaluation_previous_goal
			level = 'success' if 'success' in eval_text.lower() else 'warning' if 'failure' in eval_text.lower() else 'info'
			await self._demo_mode_log(eval_text, level, step_meta)

		if state.memory:
			await self._demo_mode_log(f'Memory: {state.memory}', 'info', step_meta)

		if state.next_goal:
			await self._demo_mode_log(f'Next goal: {state.next_goal}', 'info', step_meta)