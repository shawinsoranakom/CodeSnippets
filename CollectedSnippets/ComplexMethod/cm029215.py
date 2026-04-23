def _is_browser_closed_error(self, error: Exception) -> bool:
		"""Check if the browser has been closed or disconnected.

		Only returns True when the error itself is a CDP/WebSocket connection failure
		AND the CDP client is gone AND we're not actively reconnecting.
		Avoids false positives on unrelated errors (element not found, timeouts,
		parse errors) that happen to coincide with a transient None state during
		reconnects or resets.
		"""
		# During reconnection, don't treat connection errors as terminal
		if self.browser_session.is_reconnecting:
			return False

		error_str = str(error).lower()
		is_connection_error = (
			isinstance(error, ConnectionError)
			or 'websocket connection closed' in error_str
			or 'connection closed' in error_str
			or 'browser has been closed' in error_str
			or 'browser closed' in error_str
			or 'no browser' in error_str
		)
		return is_connection_error and self.browser_session._cdp_client_root is None