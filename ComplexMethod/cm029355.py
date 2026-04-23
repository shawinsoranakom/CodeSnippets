async def _get_or_create_session(self) -> SessionInfo:
		"""Lazy-create the single session on first command."""
		if self._session is not None:
			return self._session

		async with self._session_lock:
			# Double-check after acquiring lock
			if self._session is not None:
				return self._session

			from browser_use.skill_cli.sessions import SessionInfo, create_browser_session

			logger.info(
				f'Creating session (headed={self.headed}, profile={self.profile}, cdp_url={self.cdp_url}, use_cloud={self.use_cloud})'
			)

			self._write_state('starting')

			bs = await create_browser_session(
				self.headed,
				self.profile,
				self.cdp_url,
				use_cloud=self.use_cloud,
				cloud_profile_id=self.cloud_profile_id,
				cloud_proxy_country_code=self.cloud_proxy_country_code,
				cloud_timeout=self.cloud_timeout,
			)

			try:
				await bs.start()
				self._write_state('starting')  # refresh updated_at after bs.start() returns

				# Wait for Chrome to stabilize after CDP setup before accepting commands
				try:
					await bs.get_browser_state_summary()
				except Exception:
					pass

				# Create action handler for direct command execution (no event bus)
				from browser_use.skill_cli.actions import ActionHandler

				actions = ActionHandler(bs)

				self._session = SessionInfo(
					name=self.session,
					headed=self.headed,
					profile=self.profile,
					cdp_url=self.cdp_url,
					browser_session=bs,
					actions=actions,
					use_cloud=self.use_cloud,
				)
				self._browser_watchdog_task = asyncio.create_task(self._watch_browser())

				# Start idle timeout watchdog
				self._idle_watchdog_task = asyncio.create_task(self._watch_idle())

			except Exception:
				# Startup failed — rollback browser resources
				logger.exception('Session startup failed, rolling back')
				self._write_state('failed')
				try:
					if self.use_cloud and hasattr(bs, '_cloud_browser_client') and bs._cloud_browser_client.current_session_id:
						await asyncio.wait_for(bs._cloud_browser_client.stop_browser(), timeout=10.0)
					elif not self.cdp_url and not self.use_cloud:
						await asyncio.wait_for(bs.kill(), timeout=10.0)
					else:
						await asyncio.wait_for(bs.stop(), timeout=10.0)
				except Exception as cleanup_err:
					logger.debug(f'Rollback cleanup error: {cleanup_err}')
				raise

			self._write_state('running')
			return self._session