def agent_steps(self) -> list[str]:
		"""Format agent history as readable step descriptions for judge evaluation."""
		steps = []

		# Iterate through history items (each is an AgentHistory)
		for i, h in enumerate(self.history):
			step_text = f'Step {i + 1}:\n'

			# Get actions from model_output
			if h.model_output and h.model_output.action:
				# Use model_dump with mode='json' to serialize enums properly
				actions_list = [action.model_dump(exclude_none=True, mode='json') for action in h.model_output.action]
				action_json = json.dumps(actions_list, indent=1)
				step_text += f'Actions: {action_json}\n'

			# Get results (already a list[ActionResult] in h.result)
			if h.result:
				for j, result in enumerate(h.result):
					if result.extracted_content:
						content = str(result.extracted_content)
						step_text += f'Result {j + 1}: {content}\n'

					if result.error:
						error = str(result.error)
						step_text += f'Error {j + 1}: {error}\n'

			steps.append(step_text)

		return steps