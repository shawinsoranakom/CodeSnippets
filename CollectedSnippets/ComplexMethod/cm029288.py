async def connect(self, cdp_url: str | None = None) -> Self:
		"""Connect to a remote chromium-based browser via CDP using cdp-use.

		This MUST succeed or the browser is unusable. Fails hard on any error.
		"""

		self.browser_profile.cdp_url = cdp_url or self.cdp_url
		if not self.cdp_url:
			raise RuntimeError('Cannot setup CDP connection without CDP URL')

		# Prevent duplicate connections - clean up existing connection first
		if self._cdp_client_root is not None:
			self.logger.warning(
				'⚠️ connect() called but CDP client already exists! Cleaning up old connection before creating new one.'
			)
			try:
				await self._cdp_client_root.stop()
			except Exception as e:
				self.logger.debug(f'Error stopping old CDP client: {e}')
			self._cdp_client_root = None

		if not self.cdp_url.startswith('ws'):
			# If it's an HTTP URL, fetch the WebSocket URL from /json/version endpoint
			parsed_url = urlparse(self.cdp_url)
			path = parsed_url.path.rstrip('/')

			if not path.endswith('/json/version'):
				path = path + '/json/version'

			url = urlunparse(
				(parsed_url.scheme, parsed_url.netloc, path, parsed_url.params, parsed_url.query, parsed_url.fragment)
			)

			# Run a tiny HTTP client to query for the WebSocket URL from the /json/version endpoint
			# Default httpx timeout is 5s which can race the global wait_for(connect(), 15s).
			# Use 30s as a safety net for direct connect() callers; the wait_for is the real deadline.
			# For localhost/127.0.0.1, disable trust_env to prevent proxy env vars (HTTP_PROXY, HTTPS_PROXY)
			# from routing local requests through a proxy, which causes 502 errors on Windows.
			# Remote CDP URLs should still respect proxy settings.
			is_localhost = parsed_url.hostname in ('localhost', '127.0.0.1', '::1')
			async with httpx.AsyncClient(timeout=httpx.Timeout(30.0), trust_env=not is_localhost) as client:
				headers = dict(self.browser_profile.headers or {})
				from browser_use.utils import get_browser_use_version

				headers.setdefault('User-Agent', f'browser-use/{get_browser_use_version()}')
				version_info = await client.get(url, headers=headers)
				self.logger.debug(f'Raw version info: {str(version_info)}')
				self.browser_profile.cdp_url = version_info.json()['webSocketDebuggerUrl']

		assert self.cdp_url is not None, 'CDP URL is None.'

		browser_location = 'local browser' if self.is_local else 'remote browser'
		self.logger.debug(f'🌎 Connecting to existing chromium-based browser via CDP: {self.cdp_url} -> ({browser_location})')

		try:
			# Create and store the CDP client for direct CDP communication
			headers = dict(getattr(self.browser_profile, 'headers', None) or {})
			if not self.is_local:
				from browser_use.utils import get_browser_use_version

				headers.setdefault('User-Agent', f'browser-use/{get_browser_use_version()}')
			self._cdp_client_root = TimeoutWrappedCDPClient(
				self.cdp_url,
				additional_headers=headers or None,
				max_ws_frame_size=200 * 1024 * 1024,  # Use 200MB limit to handle pages with very large DOMs
			)
			assert self._cdp_client_root is not None
			await self._cdp_client_root.start()

			# Initialize event-driven session manager FIRST (before enabling autoAttach)
			# SessionManager will:
			# 1. Register attach/detach event handlers
			# 2. Discover and attach to all existing targets
			# 3. Initialize sessions and enable lifecycle monitoring
			# 4. Enable autoAttach for future targets
			from browser_use.browser.session_manager import SessionManager

			self.session_manager = SessionManager(self)
			await self.session_manager.start_monitoring()
			self.logger.debug('Event-driven session manager started')

			# Enable auto-attach so Chrome automatically notifies us when NEW targets attach/detach
			# This is the foundation of event-driven session management
			await self._cdp_client_root.send.Target.setAutoAttach(
				params={'autoAttach': True, 'waitForDebuggerOnStart': False, 'flatten': True}
			)
			self.logger.debug('CDP client connected with auto-attach enabled')

			# Get browser targets from SessionManager (source of truth)
			# SessionManager has already discovered all targets via start_monitoring()
			page_targets_from_manager = self.session_manager.get_all_page_targets()

			# Check for chrome://newtab pages and redirect them to about:blank (in parallel)
			from browser_use.utils import is_new_tab_page

			async def _redirect_newtab(target):
				target_url = target.url
				target_id = target.target_id
				self.logger.debug(f'🔄 Redirecting {target_url} to about:blank for target {target_id}')
				try:
					session = await self.get_or_create_cdp_session(target_id, focus=False)
					await session.cdp_client.send.Page.navigate(params={'url': 'about:blank'}, session_id=session.session_id)
					target.url = 'about:blank'
				except Exception as e:
					self.logger.warning(f'Failed to redirect {target_url}: {e}')

			redirect_tasks = [
				_redirect_newtab(target)
				for target in page_targets_from_manager
				if is_new_tab_page(target.url) and target.url != 'about:blank'
			]
			if redirect_tasks:
				await asyncio.gather(*redirect_tasks, return_exceptions=True)

			# Ensure we have at least one page
			if not page_targets_from_manager:
				new_target = await self._cdp_client_root.send.Target.createTarget(params={'url': 'about:blank'})
				target_id = new_target['targetId']
				self.logger.debug(f'📄 Created new blank page: {target_id}')
			else:
				target_id = page_targets_from_manager[0].target_id
				self.logger.debug(f'📄 Using existing page: {target_id}')

			# Set up initial focus using the public API
			# Note: get_or_create_cdp_session() will wait for attach event and set focus
			try:
				await self.get_or_create_cdp_session(target_id, focus=True)
				# agent_focus_target_id is now set by get_or_create_cdp_session
				self.logger.debug(f'📄 Agent focus set to {target_id[:8]}...')
			except ValueError as e:
				raise RuntimeError(f'Failed to get session for initial target {target_id}: {e}') from e

			# Note: Lifecycle monitoring is enabled automatically in SessionManager._handle_target_attached()
			# when targets attach, so no manual enablement needed!

			# Enable proxy authentication handling if configured
			await self._setup_proxy_auth()

			# Attach WS drop detection callback for auto-reconnection
			self._intentional_stop = False
			self._attach_ws_drop_callback()

			# Verify the target is working
			if self.agent_focus_target_id:
				target = self.session_manager.get_target(self.agent_focus_target_id)
				if target.title == 'Unknown title':
					self.logger.warning('Target created but title is unknown (may be normal for about:blank)')

			# Dispatch TabCreatedEvent for all initial tabs (so watchdogs can initialize)
			for idx, target in enumerate(page_targets_from_manager):
				target_url = target.url
				self.logger.debug(f'Dispatching TabCreatedEvent for initial tab {idx}: {target_url}')
				self.event_bus.dispatch(TabCreatedEvent(url=target_url, target_id=target.target_id))

			# Dispatch initial focus event
			if page_targets_from_manager:
				initial_url = page_targets_from_manager[0].url
				self.event_bus.dispatch(AgentFocusChangedEvent(target_id=page_targets_from_manager[0].target_id, url=initial_url))
				self.logger.debug(f'Initial agent focus set to tab 0: {initial_url}')

		except Exception as e:
			# Fatal error - browser is not usable without CDP connection
			self.logger.error(f'❌ FATAL: Failed to setup CDP connection: {e}')
			self.logger.error('❌ Browser cannot continue without CDP connection')

			# Clear SessionManager state
			if self.session_manager:
				try:
					await self.session_manager.clear()
					self.logger.debug('Cleared SessionManager state after initialization failure')
				except Exception as cleanup_error:
					self.logger.debug(f'Error clearing SessionManager: {cleanup_error}')

			# Close CDP client WebSocket and unregister handlers
			if self._cdp_client_root:
				try:
					await self._cdp_client_root.stop()  # Close WebSocket and unregister handlers
					self.logger.debug('Closed CDP client WebSocket after initialization failure')
				except Exception as cleanup_error:
					self.logger.debug(f'Error closing CDP client: {cleanup_error}')

			self.session_manager = None
			self._cdp_client_root = None
			self.agent_focus_target_id = None
			# Re-raise as a fatal error
			raise RuntimeError(f'Failed to establish CDP connection to browser: {e}') from e

		return self