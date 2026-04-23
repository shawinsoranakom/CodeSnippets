async def _handle_target_detached(self, event: DetachedFromTargetEvent) -> None:
		"""Handle Target.detachedFromTarget event.

		Called automatically by Chrome when a target/session is destroyed.
		This is the ONLY place where sessions are removed from the pool.
		"""
		session_id = event['sessionId']
		target_id = event.get('targetId')  # May be empty

		# If targetId not in event, look it up via session mapping
		if not target_id:
			async with self._lock:
				target_id = self._session_to_target.get(session_id)

		if not target_id:
			self.logger.warning(f'[SessionManager] Session detached but target unknown (session={session_id[:8]}...)')
			return

		agent_focus_lost = False
		target_fully_removed = False
		target_type = None

		async with self._lock:
			# Remove this session from target's session set
			if target_id in self._target_sessions:
				self._target_sessions[target_id].discard(session_id)

				remaining_sessions = len(self._target_sessions[target_id])

				self.logger.debug(
					f'[SessionManager] Session detached: target={target_id[:8]}... '
					f'session={session_id[:8]}... (remaining={remaining_sessions})'
				)

				# Only remove target when NO sessions remain
				if remaining_sessions == 0:
					self.logger.debug(f'[SessionManager] No sessions remain for target {target_id[:8]}..., removing target')

					target_fully_removed = True

					# Check if agent_focus points to this target
					agent_focus_lost = self.browser_session.agent_focus_target_id == target_id

					# Immediately clear stale focus to prevent operations on detached target
					if agent_focus_lost:
						self.logger.debug(
							f'[SessionManager] Clearing stale agent_focus_target_id {target_id[:8]}... '
							f'to prevent operations on detached target'
						)
						self.browser_session.agent_focus_target_id = None

					# Get target type before removing (needed for TabClosedEvent dispatch)
					target = self._targets.get(target_id)
					target_type = target.target_type if target else None

					# Remove target (entity) from owned data
					if target_id in self._targets:
						self._targets.pop(target_id)
						self.logger.debug(
							f'[SessionManager] Removed target {target_id[:8]}... (remaining targets: {len(self._targets)})'
						)

					# Clean up tracking
					del self._target_sessions[target_id]
			else:
				# Target not tracked - already removed or never attached
				self.logger.debug(
					f'[SessionManager] Session detached from untracked target: target={target_id[:8]}... '
					f'session={session_id[:8]}... (target was already removed or attach event was missed)'
				)

			# Remove session from owned sessions dict
			if session_id in self._sessions:
				self._sessions.pop(session_id)
				self.logger.debug(
					f'[SessionManager] Removed session {session_id[:8]}... (remaining sessions: {len(self._sessions)})'
				)

			# Remove from reverse mapping
			if session_id in self._session_to_target:
				del self._session_to_target[session_id]

		# Dispatch TabClosedEvent only for page/tab targets that are fully removed (not iframes/workers or partial detaches)
		if target_fully_removed:
			if target_type in ('page', 'tab'):
				from browser_use.browser.events import TabClosedEvent

				self.browser_session.event_bus.dispatch(TabClosedEvent(target_id=target_id))
				self.logger.debug(f'[SessionManager] Dispatched TabClosedEvent for page target {target_id[:8]}...')
			elif target_type:
				self.logger.debug(
					f'[SessionManager] Target {target_id[:8]}... fully removed (type={target_type}) - not dispatching TabClosedEvent'
				)

		# Auto-recover agent_focus outside the lock to avoid blocking other operations
		if agent_focus_lost:
			# Create recovery task instead of awaiting directly - allows concurrent operations to wait on same recovery
			if not self._recovery_in_progress:
				self._recovery_task = create_task_with_error_handling(
					self._recover_agent_focus(target_id),
					name='recover_agent_focus',
					logger_instance=self.logger,
					suppress_exceptions=False,
				)