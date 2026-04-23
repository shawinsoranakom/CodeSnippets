async def scroll(self, x: int = 0, y: int = 0, delta_x: int | None = None, delta_y: int | None = None) -> None:
		"""Scroll the page using robust CDP methods."""
		if not self._session_id:
			raise RuntimeError('Session ID is required for scroll operations')

		# Method 1: Try mouse wheel event (most reliable)
		try:
			# Get viewport dimensions
			layout_metrics = await self._client.send.Page.getLayoutMetrics(session_id=self._session_id)
			viewport_width = layout_metrics['layoutViewport']['clientWidth']
			viewport_height = layout_metrics['layoutViewport']['clientHeight']

			# Use provided coordinates or center of viewport
			scroll_x = x if x > 0 else viewport_width / 2
			scroll_y = y if y > 0 else viewport_height / 2

			# Calculate scroll deltas (positive = down/right)
			scroll_delta_x = delta_x or 0
			scroll_delta_y = delta_y or 0

			# Dispatch mouse wheel event
			await self._client.send.Input.dispatchMouseEvent(
				params={
					'type': 'mouseWheel',
					'x': scroll_x,
					'y': scroll_y,
					'deltaX': scroll_delta_x,
					'deltaY': scroll_delta_y,
				},
				session_id=self._session_id,
			)
			return

		except Exception:
			pass

		# Method 2: Fallback to synthesizeScrollGesture
		try:
			params: 'SynthesizeScrollGestureParameters' = {'x': x, 'y': y, 'xDistance': delta_x or 0, 'yDistance': delta_y or 0}
			await self._client.send.Input.synthesizeScrollGesture(
				params,
				session_id=self._session_id,
			)
		except Exception:
			# Method 3: JavaScript fallback
			scroll_js = f'window.scrollBy({delta_x or 0}, {delta_y or 0})'
			await self._client.send.Runtime.evaluate(
				params={'expression': scroll_js, 'returnByValue': True},
				session_id=self._session_id,
			)