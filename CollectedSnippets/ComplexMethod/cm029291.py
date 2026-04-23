async def _auto_reconnect(self, max_attempts: int = 3) -> None:
		"""Attempt to reconnect with exponential backoff.

		Dispatches BrowserReconnectingEvent before each attempt and
		BrowserReconnectedEvent on success.
		"""
		async with self._reconnect_lock:
			if self._reconnecting:
				return  # already in progress from another caller
			self._reconnecting = True
			self._reconnect_event.clear()

		start_time = time.time()
		delays = [1.0, 2.0, 4.0]

		try:
			for attempt in range(1, max_attempts + 1):
				self.event_bus.dispatch(
					BrowserReconnectingEvent(
						cdp_url=self.cdp_url or '',
						attempt=attempt,
						max_attempts=max_attempts,
					)
				)
				self.logger.warning(f'🔄 WebSocket reconnection attempt {attempt}/{max_attempts}...')

				try:
					await asyncio.wait_for(self.reconnect(), timeout=15.0)
					# Success
					downtime = time.time() - start_time
					self.event_bus.dispatch(
						BrowserReconnectedEvent(
							cdp_url=self.cdp_url or '',
							attempt=attempt,
							downtime_seconds=downtime,
						)
					)
					self.logger.info(f'🔄 WebSocket reconnected after {downtime:.1f}s (attempt {attempt})')
					return
				except Exception as e:
					self.logger.warning(f'🔄 Reconnection attempt {attempt} failed: {type(e).__name__}: {e}')
					if attempt < max_attempts:
						delay = delays[attempt - 1] if attempt - 1 < len(delays) else delays[-1]
						await asyncio.sleep(delay)

			# All attempts exhausted
			self.logger.error(f'🔄 All {max_attempts} reconnection attempts failed')
			self.event_bus.dispatch(
				BrowserErrorEvent(
					error_type='ReconnectionFailed',
					message=f'Failed to reconnect after {max_attempts} attempts ({time.time() - start_time:.1f}s)',
					details={'cdp_url': self.cdp_url or '', 'max_attempts': max_attempts},
				)
			)
		finally:
			self._reconnecting = False
			self._reconnect_event.set()