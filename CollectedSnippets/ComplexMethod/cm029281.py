async def reset(self) -> None:
		"""Clear all cached CDP sessions with proper cleanup."""

		# Suppress auto-reconnect callback during teardown
		self._intentional_stop = True
		# Cancel any in-flight reconnection task
		if self._reconnect_task and not self._reconnect_task.done():
			self._reconnect_task.cancel()
			self._reconnect_task = None
		self._reconnecting = False
		self._reconnect_event.set()  # unblock any waiters

		cdp_status = 'connected' if self._cdp_client_root else 'not connected'
		session_mgr_status = 'exists' if self.session_manager else 'None'
		self.logger.debug(
			f'🔄 Resetting browser session (CDP: {cdp_status}, SessionManager: {session_mgr_status}, '
			f'focus: {self.agent_focus_target_id[-4:] if self.agent_focus_target_id else "None"})'
		)

		# Clear session manager (which owns _targets, _sessions, _target_sessions)
		if self.session_manager:
			await self.session_manager.clear()
			self.session_manager = None

		# Close CDP WebSocket before clearing to prevent stale event handlers
		if self._cdp_client_root:
			try:
				await self._cdp_client_root.stop()
				self.logger.debug('Closed CDP client WebSocket during reset')
			except Exception as e:
				self.logger.debug(f'Error closing CDP client during reset: {e}')

		self._cdp_client_root = None  # type: ignore
		self._cached_browser_state_summary = None
		self._cached_selector_map.clear()
		self._downloaded_files.clear()

		self.agent_focus_target_id = None
		if self.is_local:
			self.browser_profile.cdp_url = None

		self._crash_watchdog = None
		self._downloads_watchdog = None
		self._aboutblank_watchdog = None
		self._security_watchdog = None
		self._storage_state_watchdog = None
		self._local_browser_watchdog = None
		self._default_action_watchdog = None
		self._dom_watchdog = None
		self._screenshot_watchdog = None
		self._permissions_watchdog = None
		self._recording_watchdog = None
		self._captcha_watchdog = None
		self._watchdogs_attached = False
		if self._demo_mode:
			self._demo_mode.reset()
			self._demo_mode = None

		self._intentional_stop = False
		self.logger.info('✅ Browser session reset complete')