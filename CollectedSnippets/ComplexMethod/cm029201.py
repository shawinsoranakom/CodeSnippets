def model_dump(self, sensitive_data: dict[str, str | dict[str, str]] | None = None, **kwargs) -> dict[str, Any]:
		"""Custom serialization handling circular references and filtering sensitive data"""

		# Handle action serialization
		model_output_dump = None
		if self.model_output:
			action_dump = [action.model_dump(exclude_none=True, mode='json') for action in self.model_output.action]

			# Filter sensitive data only from input action parameters if sensitive_data is provided
			if sensitive_data:
				action_dump = [
					self._filter_sensitive_data_from_dict(action, sensitive_data) if 'input' in action else action
					for action in action_dump
				]

			model_output_dump = {
				'evaluation_previous_goal': self.model_output.evaluation_previous_goal,
				'memory': self.model_output.memory,
				'next_goal': self.model_output.next_goal,
				'action': action_dump,  # This preserves the actual action data
			}
			# Only include thinking if it's present
			if self.model_output.thinking is not None:
				model_output_dump['thinking'] = self.model_output.thinking
			if self.model_output.current_plan_item is not None:
				model_output_dump['current_plan_item'] = self.model_output.current_plan_item
			if self.model_output.plan_update is not None:
				model_output_dump['plan_update'] = self.model_output.plan_update

		# Handle result serialization - don't filter ActionResult data
		# as it should contain meaningful information for the agent
		result_dump = [r.model_dump(exclude_none=True, mode='json') for r in self.result]

		return {
			'model_output': model_output_dump,
			'result': result_dump,
			'state': self.state.to_dict(),
			'metadata': self.metadata.model_dump() if self.metadata else None,
			'state_message': self.state_message,
		}