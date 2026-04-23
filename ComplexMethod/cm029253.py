def from_agent_step(
		cls, agent, model_output, result: list, actions_data: list[dict], browser_state_summary
	) -> 'CreateAgentStepEvent':
		"""Create a CreateAgentStepEvent from agent step data"""
		# Get first action details if available
		first_action = model_output.action[0] if model_output.action else None

		# Extract current state from model output
		current_state = model_output.current_state if hasattr(model_output, 'current_state') else None

		# Capture screenshot as base64 data URL if available
		screenshot_url = None
		if browser_state_summary.screenshot:
			screenshot_url = f'data:image/png;base64,{browser_state_summary.screenshot}'
			import logging

			logger = logging.getLogger(__name__)
			logger.debug(f'📸 Including screenshot in CreateAgentStepEvent, length: {len(browser_state_summary.screenshot)}')
		else:
			import logging

			logger = logging.getLogger(__name__)
			logger.debug('📸 No screenshot in browser_state_summary for CreateAgentStepEvent')

		return cls(
			user_id='',  # To be filled by cloud handler
			device_id=agent.cloud_sync.auth_client.device_id
			if hasattr(agent, 'cloud_sync') and agent.cloud_sync and agent.cloud_sync.auth_client
			else None,
			agent_task_id=str(agent.task_id),
			step=agent.state.n_steps,
			evaluation_previous_goal=current_state.evaluation_previous_goal if current_state else '',
			memory=current_state.memory if current_state else '',
			next_goal=current_state.next_goal if current_state else '',
			actions=actions_data,  # List of action dicts
			url=browser_state_summary.url,
			screenshot_url=screenshot_url,
		)