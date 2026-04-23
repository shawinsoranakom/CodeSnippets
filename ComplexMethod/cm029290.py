async def reconnect(self) -> None:
		"""Re-establish the CDP WebSocket connection to an already-running browser.

		This is a lightweight reconnection that:
		1. Stops the old CDPClient (WS already dead, just clean state)
		2. Clears SessionManager (all CDP sessions are invalid post-disconnect)
		3. Creates a new CDPClient with the same cdp_url
		4. Re-initializes SessionManager and re-enables autoAttach
		5. Re-discovers page targets and restores agent focus
		6. Re-enables proxy auth if configured
		"""
		assert self.cdp_url, 'Cannot reconnect without a CDP URL'

		old_focus_target_id = self.agent_focus_target_id

		# 1. Stop old CDPClient (WS is already dead, this just cleans internal state)
		if self._cdp_client_root:
			try:
				await self._cdp_client_root.stop()
			except Exception as e:
				self.logger.debug(f'Error stopping old CDP client during reconnect: {e}')
			self._cdp_client_root = None

		# 2. Clear SessionManager (all sessions are stale)
		if self.session_manager:
			try:
				await self.session_manager.clear()
			except Exception as e:
				self.logger.debug(f'Error clearing SessionManager during reconnect: {e}')
			self.session_manager = None

		self.agent_focus_target_id = None

		# 3. Create new CDPClient with the same cdp_url
		headers = dict(getattr(self.browser_profile, 'headers', None) or {})
		if not self.is_local:
			from browser_use.utils import get_browser_use_version

			headers.setdefault('User-Agent', f'browser-use/{get_browser_use_version()}')
		self._cdp_client_root = TimeoutWrappedCDPClient(
			self.cdp_url,
			additional_headers=headers or None,
			max_ws_frame_size=200 * 1024 * 1024,
		)
		await self._cdp_client_root.start()

		# 4. Re-initialize SessionManager
		from browser_use.browser.session_manager import SessionManager

		self.session_manager = SessionManager(self)
		await self.session_manager.start_monitoring()

		# 5. Re-enable autoAttach
		await self._cdp_client_root.send.Target.setAutoAttach(
			params={'autoAttach': True, 'waitForDebuggerOnStart': False, 'flatten': True}
		)

		# 6. Re-discover page targets and restore focus
		page_targets = self.session_manager.get_all_page_targets()

		# Prefer the old focus target if it still exists
		restored = False
		if old_focus_target_id:
			for target in page_targets:
				if target.target_id == old_focus_target_id:
					await self.get_or_create_cdp_session(old_focus_target_id, focus=True)
					restored = True
					self.logger.debug(f'🔄 Restored agent focus to previous target {old_focus_target_id[:8]}...')
					break

		if not restored:
			if page_targets:
				fallback_id = page_targets[0].target_id
				await self.get_or_create_cdp_session(fallback_id, focus=True)
				self.logger.debug(f'🔄 Agent focus set to fallback target {fallback_id[:8]}...')
			else:
				# No pages exist — create one
				new_target = await self._cdp_client_root.send.Target.createTarget(params={'url': 'about:blank'})
				target_id = new_target['targetId']
				await self.get_or_create_cdp_session(target_id, focus=True)
				self.logger.debug(f'🔄 Created new blank page during reconnect: {target_id[:8]}...')

		# 7. Re-enable proxy auth if configured
		await self._setup_proxy_auth()

		# 8. Attach the WS drop detection callback to the new client
		self._attach_ws_drop_callback()