async def _check_browser_health(self) -> None:
		"""Check if browser and targets are still responsive."""

		try:
			self.logger.debug(f'[CrashWatchdog] Checking browser health for target {self.browser_session.agent_focus_target_id}')
			cdp_session = await self.browser_session.get_or_create_cdp_session()

			for target in self.browser_session.session_manager.get_all_page_targets():
				if self._is_new_tab_page(target.url) and target.url != 'about:blank':
					self.logger.debug(f'[CrashWatchdog] Redirecting chrome://new-tab-page/ to about:blank {target.url}')
					cdp_session = await self.browser_session.get_or_create_cdp_session(target_id=target.target_id)
					await cdp_session.cdp_client.send.Page.navigate(
						params={'url': 'about:blank'}, session_id=cdp_session.session_id
					)

			# Quick ping to check if session is alive
			self.logger.debug(f'[CrashWatchdog] Attempting to run simple JS test expression in session {cdp_session} 1+1')
			await asyncio.wait_for(
				cdp_session.cdp_client.send.Runtime.evaluate(params={'expression': '1+1'}, session_id=cdp_session.session_id),
				timeout=1.0,
			)
			self.logger.debug(
				f'[CrashWatchdog] Browser health check passed for target {self.browser_session.agent_focus_target_id}'
			)
		except Exception as e:
			self.logger.error(
				f'[CrashWatchdog] ❌ Crashed/unresponsive session detected for target {self.browser_session.agent_focus_target_id} '
				f'error: {type(e).__name__}: {e} (Chrome will send detach event, SessionManager will auto-recover)'
			)

		# Check browser process if we have PID
		if self.browser_session._local_browser_watchdog and (proc := self.browser_session._local_browser_watchdog._subprocess):
			try:
				if proc.status() in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD):
					self.logger.error(f'[CrashWatchdog] Browser process {proc.pid} has crashed')

					# Browser process crashed - SessionManager will clean up via detach events
					# Just dispatch error event and stop monitoring
					self.event_bus.dispatch(
						BrowserErrorEvent(
							error_type='BrowserProcessCrashed',
							message=f'Browser process {proc.pid} has crashed',
							details={'pid': proc.pid, 'status': proc.status()},
						)
					)

					self.logger.warning('[CrashWatchdog] Browser process dead - stopping health monitoring')
					await self._stop_monitoring()
					return
			except Exception:
				pass