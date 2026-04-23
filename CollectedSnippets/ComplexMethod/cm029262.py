async def send_log(self, message: str, level: str = 'info', metadata: dict[str, Any] | None = None) -> None:
		"""Send a log entry to the in-browser panel."""
		if not message or not self.session.browser_profile.demo_mode:
			return

		try:
			await self.ensure_ready()
		except Exception as exc:
			self.logger.warning(f'Failed to ensure demo mode is ready: {exc}')
			return

		if self.session.agent_focus_target_id is None:
			self.logger.debug('Cannot send demo log: no active target')
			return

		level_value = level.lower()
		if level_value not in self.VALID_LEVELS:
			level_value = 'info'

		payload = {
			'message': message,
			'level': level_value,
			'metadata': metadata or {},
			'timestamp': datetime.now(timezone.utc).isoformat(),
		}

		script = self._build_event_expression(json.dumps(payload, ensure_ascii=False))

		try:
			session = await self.session.get_or_create_cdp_session(target_id=None, focus=False)
		except Exception as exc:
			self.logger.debug(f'Cannot acquire CDP session for demo log: {exc}')
			return

		try:
			await session.cdp_client.send.Runtime.evaluate(
				params={'expression': script, 'awaitPromise': False}, session_id=session.session_id
			)
		except Exception as exc:
			self.logger.debug(f'Failed to send demo log: {exc}')