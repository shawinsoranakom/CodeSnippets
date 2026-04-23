def from_agent(cls, agent) -> 'UpdateAgentTaskEvent':
		"""Create an UpdateAgentTaskEvent from an Agent instance"""
		if not hasattr(agent, '_task_start_time'):
			raise ValueError('Agent must have _task_start_time attribute')

		done_output = agent.history.final_result() if agent.history else None
		if done_output and len(done_output) > MAX_STRING_LENGTH:
			done_output = done_output[:MAX_STRING_LENGTH]
		return cls(
			id=str(agent.task_id),
			user_id='',  # To be filled by cloud handler
			device_id=agent.cloud_sync.auth_client.device_id
			if hasattr(agent, 'cloud_sync') and agent.cloud_sync and agent.cloud_sync.auth_client
			else None,
			stopped=agent.state.stopped if hasattr(agent.state, 'stopped') else False,
			paused=agent.state.paused if hasattr(agent.state, 'paused') else False,
			done_output=done_output,
			finished_at=datetime.now(timezone.utc) if agent.history and agent.history.is_done() else None,
			agent_state=agent.state.model_dump() if hasattr(agent.state, 'model_dump') else {},
			user_feedback_type=None,
			user_comment=None,
			gif_url=None,
			# user_feedback_type and user_comment would be set by the API/frontend
			# gif_url would be set after GIF generation if needed
		)