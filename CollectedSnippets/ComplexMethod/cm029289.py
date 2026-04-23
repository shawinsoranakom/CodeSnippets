async def _setup_proxy_auth(self) -> None:
		"""Enable CDP Fetch auth handling for authenticated proxy, if credentials provided.

		Handles HTTP proxy authentication challenges (Basic/Proxy) by providing
		configured credentials from BrowserProfile.
		"""

		assert self._cdp_client_root

		try:
			proxy_cfg = self.browser_profile.proxy
			username = proxy_cfg.username if proxy_cfg else None
			password = proxy_cfg.password if proxy_cfg else None
			if not username or not password:
				self.logger.debug('Proxy credentials not provided; skipping proxy auth setup')
				return

			# Enable Fetch domain with auth handling (do not pause all requests)
			try:
				await self._cdp_client_root.send.Fetch.enable(params={'handleAuthRequests': True})
				self.logger.debug('Fetch.enable(handleAuthRequests=True) enabled on root client')
			except Exception as e:
				self.logger.debug(f'Fetch.enable on root failed: {type(e).__name__}: {e}')

			# Also enable on the focused target's session if available to ensure events are delivered
			try:
				if self.agent_focus_target_id:
					cdp_session = await self.get_or_create_cdp_session(self.agent_focus_target_id, focus=False)
					await cdp_session.cdp_client.send.Fetch.enable(
						params={'handleAuthRequests': True},
						session_id=cdp_session.session_id,
					)
					self.logger.debug('Fetch.enable(handleAuthRequests=True) enabled on focused session')
			except Exception as e:
				self.logger.debug(f'Fetch.enable on focused session failed: {type(e).__name__}: {e}')

			def _on_auth_required(event: AuthRequiredEvent, session_id: SessionID | None = None):
				# event keys may be snake_case or camelCase depending on generator; handle both
				request_id = event.get('requestId') or event.get('request_id')
				if not request_id:
					return

				challenge = event.get('authChallenge') or event.get('auth_challenge') or {}
				source = (challenge.get('source') or '').lower()
				# Only respond to proxy challenges
				if source == 'proxy' and request_id:

					async def _respond():
						assert self._cdp_client_root
						try:
							await self._cdp_client_root.send.Fetch.continueWithAuth(
								params={
									'requestId': request_id,
									'authChallengeResponse': {
										'response': 'ProvideCredentials',
										'username': username,
										'password': password,
									},
								},
								session_id=session_id,
							)
						except Exception as e:
							self.logger.debug(f'Proxy auth respond failed: {type(e).__name__}: {e}')

					# schedule
					create_task_with_error_handling(
						_respond(), name='auth_respond', logger_instance=self.logger, suppress_exceptions=True
					)
				else:
					# Default behaviour for non-proxy challenges: let browser handle
					async def _default():
						assert self._cdp_client_root
						try:
							await self._cdp_client_root.send.Fetch.continueWithAuth(
								params={'requestId': request_id, 'authChallengeResponse': {'response': 'Default'}},
								session_id=session_id,
							)
						except Exception as e:
							self.logger.debug(f'Default auth respond failed: {type(e).__name__}: {e}')

					if request_id:
						create_task_with_error_handling(
							_default(), name='auth_default', logger_instance=self.logger, suppress_exceptions=True
						)

			def _on_request_paused(event: RequestPausedEvent, session_id: SessionID | None = None):
				# Continue all paused requests to avoid stalling the network
				request_id = event.get('requestId') or event.get('request_id')
				if not request_id:
					return

				async def _continue():
					assert self._cdp_client_root
					try:
						await self._cdp_client_root.send.Fetch.continueRequest(
							params={'requestId': request_id},
							session_id=session_id,
						)
					except Exception:
						pass

				create_task_with_error_handling(
					_continue(), name='request_continue', logger_instance=self.logger, suppress_exceptions=True
				)

			# Register event handler on root client
			try:
				self._cdp_client_root.register.Fetch.authRequired(_on_auth_required)
				self._cdp_client_root.register.Fetch.requestPaused(_on_request_paused)
				if self.agent_focus_target_id:
					cdp_session = await self.get_or_create_cdp_session(self.agent_focus_target_id, focus=False)
					cdp_session.cdp_client.register.Fetch.authRequired(_on_auth_required)
					cdp_session.cdp_client.register.Fetch.requestPaused(_on_request_paused)
				self.logger.debug('Registered Fetch.authRequired handlers')
			except Exception as e:
				self.logger.debug(f'Failed to register authRequired handlers: {type(e).__name__}: {e}')

			# Ensure Fetch is enabled for the current focused target's session, too
			try:
				if self.agent_focus_target_id:
					# Use safe API with focus=False to avoid changing focus
					cdp_session = await self.get_or_create_cdp_session(self.agent_focus_target_id, focus=False)
					await cdp_session.cdp_client.send.Fetch.enable(
						params={'handleAuthRequests': True, 'patterns': [{'urlPattern': '*'}]},
						session_id=cdp_session.session_id,
					)
			except Exception as e:
				self.logger.debug(f'Fetch.enable on focused session failed: {type(e).__name__}: {e}')
		except Exception as e:
			self.logger.debug(f'Skipping proxy auth setup: {type(e).__name__}: {e}')