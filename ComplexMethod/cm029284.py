async def _navigate_and_wait(
		self,
		url: str,
		target_id: str,
		timeout: float | None = None,
		wait_until: str = 'load',
		nav_timeout: float | None = None,
	) -> None:
		"""Navigate to URL and wait for page readiness using CDP lifecycle events.

		Polls stored lifecycle events (registered once per session in SessionManager).
		wait_until controls the minimum acceptable signal: 'commit', 'domcontentloaded', 'load', 'networkidle'.
		nav_timeout controls the timeout for the CDP Page.navigate() call itself (defaults to 20.0s).
		"""
		cdp_session = await self.get_or_create_cdp_session(target_id, focus=False)

		if timeout is None:
			target = self.session_manager.get_target(target_id)
			current_url = target.url
			same_domain = (
				url.split('/')[2] == current_url.split('/')[2]
				if url.startswith('http') and current_url.startswith('http')
				else False
			)
			timeout = 3.0 if same_domain else 8.0

		nav_start_time = asyncio.get_event_loop().time()

		# Wrap Page.navigate() with timeout — heavy sites can block here for 10s+
		# Use nav_timeout parameter if provided, otherwise default to 20.0
		if nav_timeout is None:
			nav_timeout = 20.0
		try:
			nav_result = await asyncio.wait_for(
				cdp_session.cdp_client.send.Page.navigate(
					params={'url': url, 'transitionType': 'address_bar'},
					session_id=cdp_session.session_id,
				),
				timeout=nav_timeout,
			)
		except TimeoutError:
			duration_ms = (asyncio.get_event_loop().time() - nav_start_time) * 1000
			raise RuntimeError(f'Page.navigate() timed out after {nav_timeout}s ({duration_ms:.0f}ms) for {url}')

		if nav_result.get('errorText'):
			raise RuntimeError(f'Navigation failed: {nav_result["errorText"]}')

		if wait_until == 'commit':
			duration_ms = (asyncio.get_event_loop().time() - nav_start_time) * 1000
			self.logger.debug(f'✅ Page ready for {url} (commit, {duration_ms:.0f}ms)')
			return

		navigation_id = nav_result.get('loaderId')
		start_time = asyncio.get_event_loop().time()
		seen_events = []

		if not hasattr(cdp_session, '_lifecycle_events'):
			raise RuntimeError(
				f'❌ Lifecycle monitoring not enabled for {cdp_session.target_id[:8]}! '
				f'This is a bug - SessionManager should have initialized it. '
				f'Session: {cdp_session}'
			)

		# Acceptable events by readiness level (higher is always acceptable)
		acceptable_events: set[str] = {'networkIdle'}
		if wait_until in ('load', 'domcontentloaded'):
			acceptable_events.add('load')
		if wait_until == 'domcontentloaded':
			acceptable_events.add('DOMContentLoaded')

		poll_interval = 0.05
		while (asyncio.get_event_loop().time() - start_time) < timeout:
			try:
				for event_data in list(cdp_session._lifecycle_events):
					event_name = event_data.get('name')
					event_loader_id = event_data.get('loaderId')

					event_str = f'{event_name}(loader={event_loader_id[:8] if event_loader_id else "none"})'
					if event_str not in seen_events:
						seen_events.append(event_str)

					if event_loader_id and navigation_id and event_loader_id != navigation_id:
						continue

					if event_name in acceptable_events:
						duration_ms = (asyncio.get_event_loop().time() - nav_start_time) * 1000
						self.logger.debug(f'✅ Page ready for {url} ({event_name}, {duration_ms:.0f}ms)')
						return

			except Exception as e:
				self.logger.debug(f'Error polling lifecycle events: {e}')

			await asyncio.sleep(poll_interval)

		duration_ms = (asyncio.get_event_loop().time() - nav_start_time) * 1000
		if not seen_events:
			self.logger.error(
				f'❌ No lifecycle events received for {url} after {duration_ms:.0f}ms! '
				f'Monitoring may have failed. Target: {cdp_session.target_id[:8]}'
			)
		else:
			self.logger.warning(f'⚠️ Page readiness timeout ({timeout}s, {duration_ms:.0f}ms) for {url}')