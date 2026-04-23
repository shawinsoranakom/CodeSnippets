async def dispatch(self, request: dict) -> dict:
		"""Route to command handlers."""
		import time

		self._last_command_time = time.monotonic()

		action = request.get('action', '')
		params = request.get('params', {})
		req_id = request.get('id', '')

		logger.info(f'Dispatch: {action} (id={req_id})')

		try:
			# Handle shutdown
			if action == 'shutdown':
				return {'id': req_id, 'success': True, 'data': {'shutdown': True}}

			# Handle ping — returns daemon config for mismatch detection
			if action == 'ping':
				# Return live CDP URL (may differ from constructor arg for cloud sessions)
				live_cdp_url = self.cdp_url
				if self._session and self._session.browser_session.cdp_url:
					live_cdp_url = self._session.browser_session.cdp_url
				return {
					'id': req_id,
					'success': True,
					'data': {
						'session': self.session,
						'pid': os.getpid(),
						'headed': self.headed,
						'profile': self.profile,
						'cdp_url': live_cdp_url,
						'use_cloud': self.use_cloud,
					},
				}

			# Handle connect — forces immediate session creation (used by cloud connect)
			if action == 'connect':
				session = await self._get_or_create_session()
				bs = session.browser_session
				result_data: dict = {'status': 'connected'}
				if bs.cdp_url:
					result_data['cdp_url'] = bs.cdp_url
				if self.use_cloud and bs.cdp_url:
					from urllib.parse import quote

					result_data['live_url'] = f'https://live.browser-use.com/?wss={quote(bs.cdp_url, safe="")}'
				return {'id': req_id, 'success': True, 'data': result_data}

			from browser_use.skill_cli.commands import browser, python_exec

			# Get or create the single session
			session = await self._get_or_create_session()

			# Dispatch to handler
			if action in browser.COMMANDS:
				result = await browser.handle(action, session, params)
			elif action == 'python':
				result = await python_exec.handle(session, params)
			else:
				return {'id': req_id, 'success': False, 'error': f'Unknown action: {action}'}

			return {'id': req_id, 'success': True, 'data': result}

		except Exception as e:
			logger.exception(f'Error dispatching {action}: {e}')
			return {'id': req_id, 'success': False, 'error': str(e)}