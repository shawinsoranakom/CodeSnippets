def _update_agent_history_description(
		self,
		model_output: AgentOutput | None = None,
		result: list[ActionResult] | None = None,
		step_info: AgentStepInfo | None = None,
	) -> None:
		"""Update the agent history description"""

		if result is None:
			result = []
		step_number = step_info.step_number if step_info else None

		self.state.read_state_description = ''
		self.state.read_state_images = []  # Clear images from previous step

		action_results = ''
		read_state_idx = 0

		for idx, action_result in enumerate(result):
			if action_result.include_extracted_content_only_once and action_result.extracted_content:
				self.state.read_state_description += (
					f'<read_state_{read_state_idx}>\n{action_result.extracted_content}\n</read_state_{read_state_idx}>\n'
				)
				read_state_idx += 1
				logger.debug(f'Added extracted_content to read_state_description: {action_result.extracted_content}')

			# Store images for one-time inclusion in the next message
			if action_result.images:
				self.state.read_state_images.extend(action_result.images)
				logger.debug(f'Added {len(action_result.images)} image(s) to read_state_images')

			if action_result.long_term_memory:
				action_results += f'{action_result.long_term_memory}\n'
				logger.debug(f'Added long_term_memory to action_results: {action_result.long_term_memory}')
			elif action_result.extracted_content and not action_result.include_extracted_content_only_once:
				action_results += f'{action_result.extracted_content}\n'
				logger.debug(f'Added extracted_content to action_results: {action_result.extracted_content}')

			if action_result.error:
				if len(action_result.error) > 200:
					error_text = action_result.error[:100] + '......' + action_result.error[-100:]
				else:
					error_text = action_result.error
				action_results += f'{error_text}\n'
				logger.debug(f'Added error to action_results: {error_text}')

		# Simple 60k character limit for read_state_description
		MAX_CONTENT_SIZE = 60000
		if len(self.state.read_state_description) > MAX_CONTENT_SIZE:
			self.state.read_state_description = (
				self.state.read_state_description[:MAX_CONTENT_SIZE] + '\n... [Content truncated at 60k characters]'
			)
			logger.debug(f'Truncated read_state_description to {MAX_CONTENT_SIZE} characters')

		self.state.read_state_description = self.state.read_state_description.strip('\n')

		if action_results:
			action_results = f'Result\n{action_results}'
		action_results = action_results.strip('\n') if action_results else None

		# Simple 60k character limit for action_results
		if action_results and len(action_results) > MAX_CONTENT_SIZE:
			action_results = action_results[:MAX_CONTENT_SIZE] + '\n... [Content truncated at 60k characters]'
			logger.debug(f'Truncated action_results to {MAX_CONTENT_SIZE} characters')

		# Build the history item
		if model_output is None:
			# Add history item for initial actions (step 0) or errors (step > 0)
			if step_number is not None:
				if step_number == 0 and action_results:
					# Step 0 with initial action results
					history_item = HistoryItem(step_number=step_number, action_results=action_results)
					self.state.agent_history_items.append(history_item)
				elif step_number > 0:
					# Error case for steps > 0
					history_item = HistoryItem(step_number=step_number, error='Agent failed to output in the right format.')
					self.state.agent_history_items.append(history_item)
		else:
			history_item = HistoryItem(
				step_number=step_number,
				evaluation_previous_goal=model_output.current_state.evaluation_previous_goal,
				memory=model_output.current_state.memory,
				next_goal=model_output.current_state.next_goal,
				action_results=action_results,
			)
			self.state.agent_history_items.append(history_item)