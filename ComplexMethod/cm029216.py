async def _finalize(self, browser_state_summary: BrowserStateSummary | None) -> None:
		"""Finalize the step with history, logging, and events"""
		step_end_time = time.time()
		if not self.state.last_result:
			return

		if browser_state_summary:
			step_interval = None
			if len(self.history.history) > 0:
				last_history_item = self.history.history[-1]

				if last_history_item.metadata:
					previous_end_time = last_history_item.metadata.step_end_time
					previous_start_time = last_history_item.metadata.step_start_time
					step_interval = max(0, previous_end_time - previous_start_time)
			metadata = StepMetadata(
				step_number=self.state.n_steps,
				step_start_time=self.step_start_time,
				step_end_time=step_end_time,
				step_interval=step_interval,
			)

			# Use _make_history_item like main branch
			await self._make_history_item(
				self.state.last_model_output,
				browser_state_summary,
				self.state.last_result,
				metadata,
				state_message=self._message_manager.last_state_message_text,
			)

		# Log step completion summary
		summary_message = self._log_step_completion_summary(self.step_start_time, self.state.last_result)
		if summary_message:
			await self._demo_mode_log(summary_message, 'info', {'step': self.state.n_steps})

		# Save file system state after step completion
		self.save_file_system_state()

		# Emit both step created and executed events
		if browser_state_summary and self.state.last_model_output:
			# Extract key step data for the event
			actions_data = []
			if self.state.last_model_output.action:
				for action in self.state.last_model_output.action:
					action_dict = action.model_dump() if hasattr(action, 'model_dump') else {}
					actions_data.append(action_dict)

			# Emit CreateAgentStepEvent
			step_event = CreateAgentStepEvent.from_agent_step(
				self,
				self.state.last_model_output,
				self.state.last_result,
				actions_data,
				browser_state_summary,
			)
			self.eventbus.dispatch(step_event)

		# Increment step counter after step is fully completed
		self.state.n_steps += 1