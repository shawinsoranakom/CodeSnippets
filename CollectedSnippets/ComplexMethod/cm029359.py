async def _shutdown(self) -> None:
		"""Graceful shutdown. Only called via _request_shutdown().

		Order matters: close the server first to release the socket/port
		immediately, so a replacement daemon can bind without waiting for
		browser cleanup. Then kill the browser session.
		"""
		logger.info('Shutting down daemon...')
		self._write_state('shutting_down')
		self.running = False
		self._shutdown_event.set()

		if self._browser_watchdog_task:
			self._browser_watchdog_task.cancel()

		if self._idle_watchdog_task:
			self._idle_watchdog_task.cancel()

		if self._server:
			self._server.close()

		if self._session:
			# Finalize any in-progress video recording before tearing down the browser,
			# otherwise the MP4 is truncated since the ffmpeg writer is never closed.
			# No timeout: stop_recording() already offloads the blocking encoder close
			# to an executor; a hard timeout here risks os._exit(0) firing before the
			# writer has flushed, producing the very truncation this hook prevents.
			bs = self._session.browser_session
			watchdog = getattr(bs, '_recording_watchdog', None)
			if watchdog is not None and getattr(watchdog, 'is_recording', False):
				try:
					saved = await watchdog.stop_recording()
					if saved:
						logger.info(f'Finalized in-progress recording: {saved}')
				except Exception as e:
					logger.warning(f'Error finalizing recording during shutdown: {e}')

			try:
				# Only kill the browser if the daemon launched it.
				# For external connections (--connect, --cdp-url, cloud), just disconnect.
				# Timeout ensures daemon exits even if CDP calls hang on a dead connection
				if self.cdp_url or self.use_cloud:
					await asyncio.wait_for(bs.stop(), timeout=10.0)
				else:
					await asyncio.wait_for(bs.kill(), timeout=10.0)
			except TimeoutError:
				logger.warning('Browser cleanup timed out after 10s, forcing exit')
			except Exception as e:
				logger.warning(f'Error closing session: {e}')
			self._session = None

		# Delete PID and auth token files last, right before exit.
		import os

		from browser_use.skill_cli.utils import get_auth_token_path, get_pid_path

		pid_path = get_pid_path(self.session)
		try:
			if pid_path.exists() and pid_path.read_text().strip() == str(os.getpid()):
				pid_path.unlink(missing_ok=True)
		except (OSError, ValueError):
			pass

		get_auth_token_path(self.session).unlink(missing_ok=True)

		self._write_state('stopped')

		# Force exit — the asyncio server's __aexit__ hangs waiting for the
		# handle_connection() call that triggered this shutdown to return.
		logger.info('Daemon process exiting')
		os._exit(0)