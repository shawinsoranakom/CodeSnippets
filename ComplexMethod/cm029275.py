async def _handle_target_attached(self, event: AttachedToTargetEvent) -> None:
		"""Handle Target.attachedToTarget event.

		Called automatically by Chrome when a new target/session is created.
		This is the ONLY place where sessions are added to the pool.
		"""
		target_id = event['targetInfo']['targetId']
		session_id = event['sessionId']
		target_type = event['targetInfo']['type']
		target_info = event['targetInfo']
		waiting_for_debugger = event.get('waitingForDebugger', False)

		self.logger.debug(
			f'[SessionManager] Target attached: {target_id[:8]}... (session={session_id[:8]}..., '
			f'type={target_type}, waitingForDebugger={waiting_for_debugger})'
		)

		# Defensive check: browser may be shutting down and _cdp_client_root could be None
		if self.browser_session._cdp_client_root is None:
			self.logger.debug(
				f'[SessionManager] Skipping target attach for {target_id[:8]}... - browser shutting down (no CDP client)'
			)
			return

		# Enable auto-attach for this session's children (do this FIRST, outside lock)
		try:
			await self.browser_session._cdp_client_root.send.Target.setAutoAttach(
				params={'autoAttach': True, 'waitForDebuggerOnStart': False, 'flatten': True}, session_id=session_id
			)
		except Exception as e:
			error_str = str(e)
			# Expected for short-lived targets (workers, temp iframes) that detach before this executes
			if '-32001' not in error_str and 'Session with given id not found' not in error_str:
				self.logger.debug(f'[SessionManager] Auto-attach failed for {target_type}: {e}')

		from browser_use.browser.session import Target

		async with self._lock:
			# Track this session for the target
			if target_id not in self._target_sessions:
				self._target_sessions[target_id] = set()

			self._target_sessions[target_id].add(session_id)
			self._session_to_target[session_id] = target_id

			# Create or update Target inside the same lock so that get_target() is never
			# called in the window between _target_sessions being set and _targets being set.
			if target_id not in self._targets:
				target = Target(
					target_id=target_id,
					target_type=target_type,
					url=target_info.get('url', 'about:blank'),
					title=target_info.get('title', 'Unknown title'),
				)
				self._targets[target_id] = target
				self.logger.debug(f'[SessionManager] Created target {target_id[:8]}... (type={target_type})')
			else:
				# Update existing target info
				existing_target = self._targets[target_id]
				existing_target.url = target_info.get('url', existing_target.url)
				existing_target.title = target_info.get('title', existing_target.title)

		# Create CDPSession (communication channel)
		from browser_use.browser.session import CDPSession

		assert self.browser_session._cdp_client_root is not None, 'Root CDP client required'

		cdp_session = CDPSession(
			cdp_client=self.browser_session._cdp_client_root,
			target_id=target_id,
			session_id=session_id,
		)

		# Add to sessions dict
		self._sessions[session_id] = cdp_session

		# If proxy auth is configured, enable Fetch auth handling on this session
		# Avoids overwriting Target.attachedToTarget handlers elsewhere
		try:
			proxy_cfg = self.browser_session.browser_profile.proxy
			username = proxy_cfg.username if proxy_cfg else None
			password = proxy_cfg.password if proxy_cfg else None
			if username and password:
				await cdp_session.cdp_client.send.Fetch.enable(
					params={'handleAuthRequests': True},
					session_id=cdp_session.session_id,
				)
				self.logger.debug(f'[SessionManager] Fetch.enable(handleAuthRequests=True) on session {session_id[:8]}...')
		except Exception as e:
			self.logger.debug(f'[SessionManager] Fetch.enable on attached session failed: {type(e).__name__}: {e}')

		self.logger.debug(
			f'[SessionManager] Created session {session_id[:8]}... for target {target_id[:8]}... '
			f'(total sessions: {len(self._sessions)})'
		)

		# Enable lifecycle events and network monitoring for page targets
		if target_type in ('page', 'tab'):
			await self._enable_page_monitoring(cdp_session)

		# Resume execution if waiting for debugger
		if waiting_for_debugger:
			try:
				assert self.browser_session._cdp_client_root is not None
				await self.browser_session._cdp_client_root.send.Runtime.runIfWaitingForDebugger(session_id=session_id)
			except Exception as e:
				self.logger.warning(f'[SessionManager] Failed to resume execution: {e}')