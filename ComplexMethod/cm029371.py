async def _provision_cloud_browser(self) -> None:
		"""Provision a cloud browser and set the CDP URL."""
		import os

		from browser_use.browser.cloud.views import CreateBrowserRequest

		# Override cloud API base URL if set (CLI injects this into daemon env).
		# CloudBrowserClient expects the host URL (it appends /api/v2/... internally).
		cloud_base = os.environ.get('BROWSER_USE_CLOUD_BASE_URL')
		if cloud_base:
			self._cloud_browser_client.api_base_url = cloud_base.rstrip('/')

		# Ensure CLI has an API key from config.json before proceeding.
		from browser_use.skill_cli.config import get_config_value

		if not get_config_value('api_key'):
			from browser_use.browser.cloud.views import CloudBrowserAuthError

			raise CloudBrowserAuthError(
				'No API key configured. Run `browser-use cloud login <key>` or `browser-use cloud signup`.'
			)

		cloud_params = self.browser_profile.cloud_browser_params or CreateBrowserRequest()
		# Set recording from CLI config (defaults to True)
		from browser_use.skill_cli.config import get_config_value

		cloud_params.enable_recording = bool(get_config_value('cloud_connect_recording'))

		try:
			cloud_response = await self._cloud_browser_client.create_browser(cloud_params)
		except Exception as e:
			# If profile is invalid, create a new one and retry once
			if 'profile' in str(e).lower() or '422' in str(e):
				logger.info('Cloud profile invalid, creating new one and retrying')
				from browser_use.skill_cli.commands.cloud import _create_cloud_profile_inner

				api_key = get_config_value('api_key')
				if not api_key:
					raise
				new_profile_id = _create_cloud_profile_inner(str(api_key))
				cloud_params.profile_id = new_profile_id
				cloud_response = await self._cloud_browser_client.create_browser(cloud_params)
			else:
				raise
		self.browser_profile.cdp_url = cloud_response.cdpUrl
		self.browser_profile.is_local = False
		logger.info(f'Cloud browser provisioned, CDP: {cloud_response.cdpUrl}')