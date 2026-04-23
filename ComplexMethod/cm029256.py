def to_string(self) -> str:
		"""Get string representation of the history item"""
		step_str = 'step' if self.step_number is not None else 'step_unknown'

		if self.error:
			return f"""<{step_str}>
{self.error}"""
		elif self.system_message:
			return self.system_message
		else:
			content_parts = []

			# Only include evaluation_previous_goal if it's not None/empty
			if self.evaluation_previous_goal:
				content_parts.append(f'{self.evaluation_previous_goal}')

			# Always include memory
			if self.memory:
				content_parts.append(f'{self.memory}')

			# Only include next_goal if it's not None/empty
			if self.next_goal:
				content_parts.append(f'{self.next_goal}')

			if self.action_results:
				content_parts.append(self.action_results)

			content = '\n'.join(content_parts)

			return f"""<{step_str}>
{content}"""