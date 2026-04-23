def from_agent(cls, agent) -> 'CreateAgentSessionEvent':
		"""Create a CreateAgentSessionEvent from an Agent instance"""
		return cls(
			id=str(agent.session_id),
			user_id='',  # To be filled by cloud handler
			device_id=agent.cloud_sync.auth_client.device_id
			if hasattr(agent, 'cloud_sync') and agent.cloud_sync and agent.cloud_sync.auth_client
			else None,
			browser_session_id=agent.browser_session.id,
			browser_session_live_url='',  # To be filled by cloud handler
			browser_session_cdp_url='',  # To be filled by cloud handler
			browser_state={
				'viewport': agent.browser_profile.viewport if agent.browser_profile else {'width': 1280, 'height': 720},
				'user_agent': agent.browser_profile.user_agent if agent.browser_profile else None,
				'headless': agent.browser_profile.headless if agent.browser_profile else True,
				'initial_url': None,  # Will be updated during execution
				'final_url': None,  # Will be updated during execution
				'total_pages_visited': 0,  # Will be updated during execution
				'session_duration_seconds': 0,  # Will be updated during execution
			},
			browser_session_data={
				'cookies': [],
				'secrets': {},
				# TODO: send secrets safely so tasks can be replayed on cloud seamlessly
				# 'secrets': dict(agent.sensitive_data) if agent.sensitive_data else {},
				'allowed_domains': agent.browser_profile.allowed_domains if agent.browser_profile else [],
			},
		)