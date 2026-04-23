async def create_browser(
		self, request: CreateBrowserRequest, extra_headers: dict[str, str] | None = None
	) -> CloudBrowserResponse:
		"""Create a new cloud browser instance. For full docs refer to https://docs.cloud.browser-use.com/api-reference/v-2-api-current/browsers/create-browser-session-browsers-post

		Args:
			request: CreateBrowserRequest object containing browser creation parameters

		Returns:
			CloudBrowserResponse: Contains CDP URL and other browser info
		"""
		url = f'{self.api_base_url}/api/v2/browsers'

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

		# Convert request to dictionary and exclude unset fields
		request_body = request.model_dump(exclude_unset=True)

		try:
			logger.info('🌤️ Creating cloud browser instance...')

			response = await self.client.post(url, headers=headers, json=request_body)

			if response.status_code == 401:
				raise CloudBrowserAuthError(
					'BROWSER_USE_API_KEY is invalid. Get a new key at:\n'
					'https://cloud.browser-use.com/new-api-key?utm_source=oss&utm_medium=use_cloud'
				)
			elif response.status_code == 403:
				raise CloudBrowserAuthError('Access forbidden. Please check your browser-use cloud subscription status.')
			elif not response.is_success:
				error_msg = f'Failed to create cloud browser: HTTP {response.status_code}'
				try:
					error_data = response.json()
					if 'detail' in error_data:
						error_msg += f' - {error_data["detail"]}'
				except Exception:
					pass
				raise CloudBrowserError(error_msg)

			browser_data = response.json()
			browser_response = CloudBrowserResponse(**browser_data)

			# Store session ID for cleanup
			self.current_session_id = browser_response.id

			logger.info(f'🌤️ Cloud browser created successfully: {browser_response.id}')
			logger.debug(f'🌤️ CDP URL: {browser_response.cdpUrl}')
			# Cyan color for live URL
			logger.info(f'\033[36m🔗 Live URL: {browser_response.liveUrl}\033[0m')

			return browser_response

		except httpx.TimeoutException:
			raise CloudBrowserError('Timeout while creating cloud browser. Please try again.')
		except httpx.ConnectError:
			raise CloudBrowserError('Failed to connect to cloud browser service. Please check your internet connection.')
		except Exception as e:
			if isinstance(e, (CloudBrowserError, CloudBrowserAuthError)):
				raise
			raise CloudBrowserError(f'Unexpected error creating cloud browser: {e}')