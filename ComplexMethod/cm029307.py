async def stop_browser(
		self, session_id: str | None = None, extra_headers: dict[str, str] | None = None
	) -> CloudBrowserResponse:
		"""Stop a cloud browser session.

		Args:
			session_id: Session ID to stop. If None, uses current session.

		Returns:
			CloudBrowserResponse: Updated browser info with stopped status

		Raises:
			CloudBrowserAuthError: If authentication fails
			CloudBrowserError: If stopping fails
		"""
		if session_id is None:
			session_id = self.current_session_id

		if not session_id:
			raise CloudBrowserError('No session ID provided and no current session available')

		url = f'{self.api_base_url}/api/v2/browsers/{session_id}'

		# Try to get API key from environment variable first, then auth config
		api_token = os.getenv('BROWSER_USE_API_KEY')

		if not api_token:
			# Fallback to auth config file
			try:
				auth_config = CloudAuthConfig.load_from_file()
				api_token = auth_config.api_token
			except Exception:
				pass

		if not api_token:
			raise CloudBrowserAuthError(
				'BROWSER_USE_API_KEY is not set. To use cloud browsers, get a key at:\n'
				'https://cloud.browser-use.com/new-api-key?utm_source=oss&utm_medium=use_cloud'
			)

		headers = {'X-Browser-Use-API-Key': api_token, 'Content-Type': 'application/json', **(extra_headers or {})}

		request_body = {'action': 'stop'}

		try:
			logger.info(f'🌤️ Stopping cloud browser session: {session_id}')

			response = await self.client.patch(url, headers=headers, json=request_body)

			if response.status_code == 401:
				raise CloudBrowserAuthError(
					'Authentication failed. Please make sure you have set the BROWSER_USE_API_KEY environment variable to authenticate with the cloud service.'
				)
			elif response.status_code == 404:
				# Session already stopped or doesn't exist - treating as error and clearing session
				logger.debug(f'🌤️ Cloud browser session {session_id} not found (already stopped)')
				# Clear current session if it was this one
				if session_id == self.current_session_id:
					self.current_session_id = None
				raise CloudBrowserError(f'Cloud browser session {session_id} not found')
			elif not response.is_success:
				error_msg = f'Failed to stop cloud browser: HTTP {response.status_code}'
				try:
					error_data = response.json()
					if 'detail' in error_data:
						error_msg += f' - {error_data["detail"]}'
				except Exception:
					pass
				raise CloudBrowserError(error_msg)

			browser_data = response.json()
			browser_response = CloudBrowserResponse(**browser_data)

			# Clear current session if it was this one
			if session_id == self.current_session_id:
				self.current_session_id = None

			logger.info(f'🌤️ Cloud browser session stopped: {browser_response.id}')
			logger.debug(f'🌤️ Status: {browser_response.status}')

			return browser_response

		except httpx.TimeoutException:
			raise CloudBrowserError('Timeout while stopping cloud browser. Please try again.')
		except httpx.ConnectError:
			raise CloudBrowserError('Failed to connect to cloud browser service. Please check your internet connection.')
		except Exception as e:
			if isinstance(e, (CloudBrowserError, CloudBrowserAuthError)):
				raise
			raise CloudBrowserError(f'Unexpected error stopping cloud browser: {e}')