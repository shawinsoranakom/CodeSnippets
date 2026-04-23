async def on_BrowserStopEvent(self, event: BrowserStopEvent) -> None:
		"""Handle browser stop request."""

		try:
			# Check if we should keep the browser alive
			if self.browser_profile.keep_alive and not event.force:
				self.event_bus.dispatch(BrowserStoppedEvent(reason='Kept alive due to keep_alive=True'))
				return

			# Clean up cloud browser session for both:
			# 1) native use_cloud sessions (current_session_id set by create_browser)
			# 2) reconnected cdp_url sessions (derive UUID from host)
			cloud_session_id = self._cloud_browser_client.current_session_id or self._cloud_session_id_from_cdp_url()
			if cloud_session_id:
				try:
					await self._cloud_browser_client.stop_browser(cloud_session_id)
					self.logger.info(f'🌤️ Cloud browser session cleaned up: {cloud_session_id}')
				except Exception as e:
					self.logger.debug(f'Failed to cleanup cloud browser session {cloud_session_id}: {e}')
				finally:
					# Always close the httpx client to free connection pool memory
					try:
						await self._cloud_browser_client.close()
					except Exception:
						pass

			# Clear CDP session cache before stopping
			self.logger.info(
				f'📢 on_BrowserStopEvent - Calling reset() (force={event.force}, keep_alive={self.browser_profile.keep_alive})'
			)
			await self.reset()

			# Reset state
			if self.is_local:
				self.browser_profile.cdp_url = None

			# Notify stop and wait for all handlers to complete
			# LocalBrowserWatchdog listens for BrowserStopEvent and dispatches BrowserKillEvent
			stop_event = self.event_bus.dispatch(BrowserStoppedEvent(reason='Stopped by request'))
			await stop_event

		except Exception as e:
			self.event_bus.dispatch(
				BrowserErrorEvent(
					error_type='BrowserStopEventError',
					message=f'Failed to stop browser: {type(e).__name__} {e}',
					details={'cdp_url': self.cdp_url, 'is_local': self.is_local},
				)
			)