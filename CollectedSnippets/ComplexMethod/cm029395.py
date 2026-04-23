async def authenticate(
		self,
		agent_session_id: str | None = None,
		show_instructions: bool = True,
	) -> bool:
		"""
		Run the full authentication flow.
		Returns True if authentication successful.
		"""
		import logging

		logger = logging.getLogger(__name__)

		try:
			# Start device authorization
			device_auth = await self.start_device_authorization(agent_session_id)

			# Use frontend URL for user-facing links
			frontend_url = CONFIG.BROWSER_USE_CLOUD_UI_URL or self.base_url.replace('//api.', '//cloud.')

			# Replace backend URL with frontend URL in verification URIs
			verification_uri = device_auth['verification_uri'].replace(self.base_url, frontend_url)
			verification_uri_complete = device_auth['verification_uri_complete'].replace(self.base_url, frontend_url)

			terminal_width, _terminal_height = shutil.get_terminal_size((80, 20))
			if show_instructions and CONFIG.BROWSER_USE_CLOUD_SYNC:
				logger.info('─' * max(terminal_width - 40, 20))
				logger.info('🌐  View the details of this run in Browser Use Cloud:')
				logger.info(f'    👉  {verification_uri_complete}')
				logger.info('─' * max(terminal_width - 40, 20) + '\n')

			# Poll for token
			token_data = await self.poll_for_token(
				device_code=device_auth['device_code'],
				interval=device_auth.get('interval', 5),
			)

			if token_data and token_data.get('access_token'):
				# Save authentication
				self.auth_config.api_token = token_data['access_token']
				self.auth_config.user_id = token_data.get('user_id', self.temp_user_id)
				self.auth_config.authorized_at = datetime.now()
				self.auth_config.save_to_file()

				if show_instructions:
					logger.debug('✅  Authentication successful! Cloud sync is now enabled with your browser-use account.')

				return True

		except httpx.HTTPStatusError as e:
			# HTTP error with response
			if e.response.status_code == 404:
				logger.warning(
					'Cloud sync authentication endpoint not found (404). Check your BROWSER_USE_CLOUD_API_URL setting.'
				)
			else:
				logger.warning(f'Failed to authenticate with cloud service: HTTP {e.response.status_code} - {e.response.text}')
		except httpx.RequestError as e:
			# Connection/network errors
			# logger.warning(f'Failed to connect to cloud service: {type(e).__name__}: {e}')
			pass
		except Exception as e:
			# Other unexpected errors
			logger.warning(f'❌ Unexpected error during cloud sync authentication: {type(e).__name__}: {e}')

		if show_instructions:
			logger.debug(f'❌ Sync authentication failed or timed out with {CONFIG.BROWSER_USE_CLOUD_API_URL}')

		return False