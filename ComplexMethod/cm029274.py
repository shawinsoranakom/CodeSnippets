async def ensure_valid_focus(self, timeout: float = 3.0) -> bool:
		"""Ensure agent_focus_target_id points to a valid, attached CDP session.

		If the focus target is stale (detached), this method waits for automatic recovery.
		Uses event-driven coordination instead of polling for efficiency.

		Args:
			timeout: Maximum time to wait for recovery in seconds (default: 3.0)

		Returns:
			True if focus is valid or successfully recovered, False if no focus or recovery failed
		"""
		if not self.browser_session.agent_focus_target_id:
			# No focus at all - might be initial state or complete failure
			if self._recovery_in_progress and self._recovery_complete_event:
				# Recovery is happening, wait for it
				try:
					await asyncio.wait_for(self._recovery_complete_event.wait(), timeout=timeout)
					# Check again after recovery - simple existence check
					focus_id = self.browser_session.agent_focus_target_id
					return bool(focus_id and self._get_session_for_target(focus_id))
				except TimeoutError:
					self.logger.error(f'[SessionManager] ❌ Timed out waiting for recovery after {timeout}s')
					return False
			return False

		# Simple existence check - does the focused target have a session?
		cdp_session = self._get_session_for_target(self.browser_session.agent_focus_target_id)
		if cdp_session:
			# Session exists - validate it's still active
			is_valid = await self.validate_session(self.browser_session.agent_focus_target_id)
			if is_valid:
				return True

		# Focus is stale - wait for recovery using event instead of polling
		stale_target_id = self.browser_session.agent_focus_target_id
		self.logger.warning(
			f'[SessionManager] ⚠️ Stale agent_focus detected (target {stale_target_id[:8] if stale_target_id else "None"}... detached), '
			f'waiting for recovery...'
		)

		# Check if recovery is already in progress
		if not self._recovery_in_progress:
			self.logger.warning(
				'[SessionManager] ⚠️ Recovery not in progress for stale focus! '
				'This indicates a bug - recovery should have been triggered.'
			)
			return False

		# Wait for recovery complete event (event-driven, not polling!)
		if self._recovery_complete_event:
			try:
				start_time = asyncio.get_event_loop().time()
				await asyncio.wait_for(self._recovery_complete_event.wait(), timeout=timeout)
				elapsed = asyncio.get_event_loop().time() - start_time

				# Verify recovery succeeded - simple existence check
				focus_id = self.browser_session.agent_focus_target_id
				if focus_id and self._get_session_for_target(focus_id):
					self.logger.info(
						f'[SessionManager] ✅ Agent focus recovered to {self.browser_session.agent_focus_target_id[:8]}... '
						f'after {elapsed * 1000:.0f}ms'
					)
					return True
				else:
					self.logger.error(
						f'[SessionManager] ❌ Recovery completed but focus still invalid after {elapsed * 1000:.0f}ms'
					)
					return False

			except TimeoutError:
				self.logger.error(
					f'[SessionManager] ❌ Recovery timed out after {timeout}s '
					f'(was: {stale_target_id[:8] if stale_target_id else "None"}..., '
					f'now: {self.browser_session.agent_focus_target_id[:8] if self.browser_session.agent_focus_target_id else "None"})'
				)
				return False
		else:
			self.logger.error('[SessionManager] ❌ Recovery event not initialized')
			return False