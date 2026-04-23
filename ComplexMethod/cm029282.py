async def on_BrowserStartEvent(self, event: BrowserStartEvent) -> dict[str, str]:
		"""Handle browser start request.

		Returns:
			Dict with 'cdp_url' key containing the CDP URL

		Note: This method is idempotent - calling start() multiple times is safe.
		- If already connected, it skips reconnection
		- If you need to reset state, call stop() or kill() first
		"""

		# Initialize and attach all watchdogs FIRST so LocalBrowserWatchdog can handle BrowserLaunchEvent
		await self.attach_all_watchdogs()

		try:
			# If no CDP URL, launch local browser or cloud browser
			if not self.cdp_url:
				if self.browser_profile.use_cloud or self.browser_profile.cloud_browser_params is not None:
					# Use cloud browser service
					try:
						# Use cloud_browser_params if provided, otherwise create empty request
						cloud_params = self.browser_profile.cloud_browser_params or CreateBrowserRequest()
						cloud_browser_response = await self._cloud_browser_client.create_browser(cloud_params)
						self.browser_profile.cdp_url = cloud_browser_response.cdpUrl
						self.browser_profile.is_local = False
						self.logger.info('🌤️ Successfully connected to cloud browser service')
					except CloudBrowserAuthError:
						raise
					except CloudBrowserError as e:
						raise CloudBrowserError(f'Failed to create cloud browser: {e}')
				elif self.is_local:
					# Launch local browser using event-driven approach
					launch_event = self.event_bus.dispatch(BrowserLaunchEvent())
					await launch_event

					# Get the CDP URL from LocalBrowserWatchdog handler result
					launch_result: BrowserLaunchResult = cast(
						BrowserLaunchResult, await launch_event.event_result(raise_if_none=True, raise_if_any=True)
					)
					self.browser_profile.cdp_url = launch_result.cdp_url
				else:
					raise ValueError('Got BrowserSession(is_local=False) but no cdp_url was provided to connect to!')

			assert self.cdp_url and '://' in self.cdp_url

			# Use lock to prevent concurrent connection attempts (race condition protection)
			async with self._connection_lock:
				# Only connect if not already connected
				if self._cdp_client_root is None:
					# Setup browser via CDP (for both local and remote cases)
					# Global timeout prevents connect() from hanging indefinitely on
					# slow/broken WebSocket connections (common on Lambda → remote browser)
					try:
						await asyncio.wait_for(self.connect(cdp_url=self.cdp_url), timeout=15.0)
					except TimeoutError:
						# Timeout cancels connect() via CancelledError, which bypasses
						# connect()'s `except Exception` cleanup (CancelledError is BaseException).
						# Clean up the partially-initialized client so future start attempts
						# don't skip reconnection due to _cdp_client_root being non-None.
						cdp_client = cast(CDPClient | None, self._cdp_client_root)
						if cdp_client is not None:
							try:
								await cdp_client.stop()
							except Exception:
								pass
							self._cdp_client_root = None
						manager = self.session_manager
						if manager is not None:
							try:
								await manager.clear()
							except Exception:
								pass
							self.session_manager = None
						self.agent_focus_target_id = None
						raise RuntimeError(
							f'connect() timed out after 15s — CDP connection to {self.cdp_url} is too slow or unresponsive'
						)
					assert self.cdp_client is not None

					# Notify that browser is connected (single place)
					# Ensure BrowserConnected handlers (storage_state restore) complete before
					# start() returns so cookies/storage are applied before navigation.
					await self.event_bus.dispatch(BrowserConnectedEvent(cdp_url=self.cdp_url))

					if self.browser_profile.demo_mode:
						try:
							demo = self.demo_mode
							if demo:
								await demo.ensure_ready()
						except Exception as exc:
							self.logger.warning(f'[DemoMode] Failed to inject demo overlay: {exc}')
				else:
					self.logger.debug('Already connected to CDP, skipping reconnection')
					if self.browser_profile.demo_mode:
						try:
							demo = self.demo_mode
							if demo:
								await demo.ensure_ready()
						except Exception as exc:
							self.logger.warning(f'[DemoMode] Failed to inject demo overlay: {exc}')

			# Return the CDP URL for other components
			return {'cdp_url': self.cdp_url}

		except Exception as e:
			self.event_bus.dispatch(
				BrowserErrorEvent(
					error_type='BrowserStartEventError',
					message=f'Failed to start browser: {type(e).__name__} {e}',
					details={'cdp_url': self.cdp_url, 'is_local': self.is_local},
				)
			)
			if self.is_local and not isinstance(e, (CloudBrowserAuthError, CloudBrowserError)):
				self.logger.warning(
					'Local browser failed to start. Cloud browsers require no local install and work out of the box.\n'
					'         Try: Browser(use_cloud=True)  |  Get an API key: https://cloud.browser-use.com?utm_source=oss&utm_medium=browser_launch_failure'
				)
			raise