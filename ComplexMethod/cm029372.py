async def stop(self) -> None:
		"""Disconnect from the browser.

		For --connect/--cdp-url: just close the websocket (we don't own the browser).
		For cloud: stop the remote browser via API before disconnecting.
		"""
		self._intentional_stop = True
		# Stop cloud browser if we provisioned one
		if self.browser_profile.use_cloud and self._cloud_browser_client.current_session_id:
			try:
				import asyncio as _asyncio

				await _asyncio.wait_for(self._cloud_browser_client.stop_browser(), timeout=5.0)
			except Exception as e:
				logger.debug(f'Error stopping cloud browser: {e}')
		if self._cdp_client_root:
			try:
				await self._cdp_client_root.stop()
			except Exception as e:
				logger.debug(f'Error closing CDP client: {e}')
			self._cdp_client_root = None  # type: ignore[assignment]
		if self.session_manager:
			try:
				await self.session_manager.clear()
			except Exception as e:
				logger.debug(f'Error clearing session manager: {e}')
			self.session_manager = None
		self.agent_focus_target_id = None
		self._cached_selector_map.clear()