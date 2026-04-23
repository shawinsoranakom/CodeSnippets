async def _initialize_existing_targets(self) -> None:
		"""Discover and initialize all existing targets at startup.

		Attaches to each target and initializes it SYNCHRONOUSLY.
		Chrome will also fire attachedToTarget events, but _handle_target_attached() is
		idempotent (checks if target already in pool), so duplicate handling is safe.

		This eliminates race conditions - monitoring is guaranteed ready before navigation.
		"""
		cdp_client = self.browser_session._cdp_client_root
		assert cdp_client is not None

		# Get all existing targets
		targets_result = await cdp_client.send.Target.getTargets()
		existing_targets = targets_result.get('targetInfos', [])

		self.logger.debug(f'[SessionManager] Discovered {len(existing_targets)} existing targets')

		# Track target IDs for verification
		target_ids_to_wait_for = []

		# Just attach to ALL existing targets - Chrome fires attachedToTarget events
		# The on_attached handler (via create_task) does ALL the work
		for target in existing_targets:
			target_id = target['targetId']
			target_type = target.get('type', 'unknown')

			try:
				# Just attach - event handler does everything
				await cdp_client.send.Target.attachToTarget(params={'targetId': target_id, 'flatten': True})
				target_ids_to_wait_for.append(target_id)
			except Exception as e:
				self.logger.debug(
					f'[SessionManager] Failed to attach to existing target {target_id[:8]}... (type={target_type}): {e}'
				)

		# Wait for event handlers to complete their work (they run via create_task)
		# Use event-driven approach instead of polling for better performance
		ready_event = asyncio.Event()

		async def check_all_ready():
			"""Check if all sessions are ready and signal completion."""
			while True:
				ready_count = 0
				for tid in target_ids_to_wait_for:
					session = self._get_session_for_target(tid)
					if session:
						target = self._targets.get(tid)
						target_type = target.target_type if target else 'unknown'
						# For pages, verify monitoring is enabled
						if target_type in ('page', 'tab'):
							if hasattr(session, '_lifecycle_events') and session._lifecycle_events is not None:
								ready_count += 1
						else:
							# Non-page targets don't need monitoring
							ready_count += 1

				if ready_count == len(target_ids_to_wait_for):
					ready_event.set()
					return

				await asyncio.sleep(0.05)

		# Start checking in background
		check_task = create_task_with_error_handling(
			check_all_ready(), name='check_all_targets_ready', logger_instance=self.logger
		)

		try:
			# Wait for completion with timeout
			await asyncio.wait_for(ready_event.wait(), timeout=2.0)
		except TimeoutError:
			# Timeout - count what's ready
			ready_count = 0
			for tid in target_ids_to_wait_for:
				session = self._get_session_for_target(tid)
				if session:
					target = self._targets.get(tid)
					target_type = target.target_type if target else 'unknown'
					# For pages, verify monitoring is enabled
					if target_type in ('page', 'tab'):
						if hasattr(session, '_lifecycle_events') and session._lifecycle_events is not None:
							ready_count += 1
					else:
						# Non-page targets don't need monitoring
						ready_count += 1
			self.logger.warning(
				f'[SessionManager] Initialization timeout after 2.0s: {ready_count}/{len(target_ids_to_wait_for)} sessions ready'
			)
		finally:
			check_task.cancel()
			try:
				await check_task
			except asyncio.CancelledError:
				pass