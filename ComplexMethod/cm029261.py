def create_state_messages(
		self,
		browser_state_summary: BrowserStateSummary,
		model_output: AgentOutput | None = None,
		result: list[ActionResult] | None = None,
		step_info: AgentStepInfo | None = None,
		use_vision: bool | Literal['auto'] = True,
		page_filtered_actions: str | None = None,
		sensitive_data=None,
		available_file_paths: list[str] | None = None,  # Always pass current available_file_paths
		unavailable_skills_info: str | None = None,  # Information about skills that cannot be used yet
		plan_description: str | None = None,  # Rendered plan for injection into agent state
		skip_state_update: bool = False,
	) -> None:
		"""Create single state message with all content"""

		if not skip_state_update:
			self.prepare_step_state(
				browser_state_summary=browser_state_summary,
				model_output=model_output,
				result=result,
				step_info=step_info,
				sensitive_data=sensitive_data,
			)

		# Use only the current screenshot, but check if action results request screenshot inclusion
		screenshots = []
		include_screenshot_requested = False

		# Check if any action results request screenshot inclusion
		if result:
			for action_result in result:
				if action_result.metadata and action_result.metadata.get('include_screenshot'):
					include_screenshot_requested = True
					logger.debug('Screenshot inclusion requested by action result')
					break

		# Handle different use_vision modes:
		# - "auto": Only include screenshot if explicitly requested by action (e.g., screenshot)
		# - True: Always include screenshot
		# - False: Never include screenshot
		include_screenshot = False
		if use_vision is True:
			# Always include screenshot when use_vision=True
			include_screenshot = True
		elif use_vision == 'auto':
			# Only include screenshot if explicitly requested by action when use_vision="auto"
			include_screenshot = include_screenshot_requested
		# else: use_vision is False, never include screenshot (include_screenshot stays False)

		if include_screenshot and browser_state_summary.screenshot:
			screenshots.append(browser_state_summary.screenshot)

		# Use vision in the user message if screenshots are included
		effective_use_vision = len(screenshots) > 0

		# Create single state message with all content
		assert browser_state_summary
		state_message = AgentMessagePrompt(
			browser_state_summary=browser_state_summary,
			file_system=self.file_system,
			agent_history_description=self.agent_history_description,
			read_state_description=self.state.read_state_description,
			task=self.task,
			include_attributes=self.include_attributes,
			step_info=step_info,
			page_filtered_actions=page_filtered_actions,
			max_clickable_elements_length=self.max_clickable_elements_length,
			sensitive_data=self.sensitive_data_description,
			available_file_paths=available_file_paths,
			screenshots=screenshots,
			vision_detail_level=self.vision_detail_level,
			include_recent_events=self.include_recent_events,
			sample_images=self.sample_images,
			read_state_images=self.state.read_state_images,
			llm_screenshot_size=self.llm_screenshot_size,
			unavailable_skills_info=unavailable_skills_info,
			plan_description=plan_description,
		).get_user_message(effective_use_vision)

		# Store state message text for history
		self.last_state_message_text = state_message.text

		# Set the state message with caching enabled
		self._set_message_with_type(state_message, 'state')