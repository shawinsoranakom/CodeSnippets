async def _recover_agent_focus(self, crashed_target_id: TargetID) -> None:
		"""Auto-recover agent_focus when the focused target crashes/detaches.

		Uses recovery lock to prevent concurrent recovery attempts from creating multiple emergency tabs.
		Coordinates with ensure_valid_focus() via events for efficient waiting.

		Args:
			crashed_target_id: The target ID that was lost
		"""
		try:
			# Prevent concurrent recovery attempts
			async with self._recovery_lock:
				# Set recovery state INSIDE lock to prevent race conditions
				if self._recovery_in_progress:
					self.logger.debug('[SessionManager] Recovery already in progress, waiting for it to complete')
					# Wait for ongoing recovery instead of starting a new one
					if self._recovery_complete_event:
						try:
							await asyncio.wait_for(self._recovery_complete_event.wait(), timeout=5.0)
						except TimeoutError:
							self.logger.error('[SessionManager] Timed out waiting for ongoing recovery')
					return

				# Set recovery state
				self._recovery_in_progress = True
				self._recovery_complete_event = asyncio.Event()

				if self.browser_session._cdp_client_root is None:
					self.logger.debug('[SessionManager] Skipping focus recovery - browser shutting down (no CDP client)')
					return

				# Check if another recovery already fixed agent_focus
				if self.browser_session.agent_focus_target_id and self.browser_session.agent_focus_target_id != crashed_target_id:
					self.logger.debug(
						f'[SessionManager] Agent focus already recovered by concurrent operation '
						f'(now: {self.browser_session.agent_focus_target_id[:8]}...), skipping recovery'
					)
					return

				# Note: agent_focus_target_id may already be None (cleared in _handle_target_detached)
				current_focus_desc = (
					f'{self.browser_session.agent_focus_target_id[:8]}...'
					if self.browser_session.agent_focus_target_id
					else 'None (already cleared)'
				)

				self.logger.warning(
					f'[SessionManager] Agent focus target {crashed_target_id[:8]}... detached! '
					f'Current focus: {current_focus_desc}. Auto-recovering by switching to another target...'
				)

			# Perform recovery (outside lock to allow concurrent operations)
			# Try to find another valid page target
			page_targets = self.get_all_page_targets()

			new_target_id = None
			is_existing_tab = False

			if page_targets:
				# Switch to most recent page that's not the crashed one
				new_target_id = page_targets[-1].target_id
				is_existing_tab = True
				self.logger.info(f'[SessionManager] Switching agent_focus to existing tab {new_target_id[:8]}...')
			else:
				# No pages exist - create a new one
				self.logger.warning('[SessionManager] No tabs remain! Creating new tab for agent...')
				new_target_id = await self.browser_session._cdp_create_new_page('about:blank')
				self.logger.info(f'[SessionManager] Created new tab {new_target_id[:8]}... for agent')

				# Dispatch TabCreatedEvent so watchdogs can initialize
				from browser_use.browser.events import TabCreatedEvent

				self.browser_session.event_bus.dispatch(TabCreatedEvent(url='about:blank', target_id=new_target_id))

			# Wait for CDP attach event to create session
			# Note: This polling is necessary - waiting for external Chrome CDP event
			# _handle_target_attached will add session to pool when Chrome fires attachedToTarget
			new_session = None
			for attempt in range(20):  # Wait up to 2 seconds
				await asyncio.sleep(0.1)
				new_session = self._get_session_for_target(new_target_id)
				if new_session:
					break

			if new_session:
				self.browser_session.agent_focus_target_id = new_target_id
				self.logger.info(f'[SessionManager] ✅ Agent focus recovered: {new_target_id[:8]}...')

				# Visually activate the tab in browser (only for existing tabs)
				if is_existing_tab:
					try:
						assert self.browser_session._cdp_client_root is not None
						await self.browser_session._cdp_client_root.send.Target.activateTarget(params={'targetId': new_target_id})
						self.logger.debug(f'[SessionManager] Activated tab {new_target_id[:8]}... in browser UI')
					except Exception as e:
						self.logger.debug(f'[SessionManager] Failed to activate tab visually: {e}')

				# Get target to access url (from owned data)
				target = self.get_target(new_target_id)
				target_url = target.url if target else 'about:blank'

				# Dispatch focus changed event
				from browser_use.browser.events import AgentFocusChangedEvent

				self.browser_session.event_bus.dispatch(AgentFocusChangedEvent(target_id=new_target_id, url=target_url))
				return

			# Recovery failed - create emergency fallback tab
			self.logger.error(
				f'[SessionManager] ❌ Failed to get session for {new_target_id[:8]}... after 2s, creating emergency fallback tab'
			)

			fallback_target_id = await self.browser_session._cdp_create_new_page('about:blank')
			self.logger.warning(f'[SessionManager] Created emergency fallback tab {fallback_target_id[:8]}...')

			# Try one more time with fallback
			# Note: This polling is necessary - waiting for external Chrome CDP event
			for _ in range(20):
				await asyncio.sleep(0.1)
				fallback_session = self._get_session_for_target(fallback_target_id)
				if fallback_session:
					self.browser_session.agent_focus_target_id = fallback_target_id
					self.logger.warning(f'[SessionManager] ⚠️ Agent focus set to emergency fallback: {fallback_target_id[:8]}...')

					from browser_use.browser.events import AgentFocusChangedEvent, TabCreatedEvent

					self.browser_session.event_bus.dispatch(TabCreatedEvent(url='about:blank', target_id=fallback_target_id))
					self.browser_session.event_bus.dispatch(
						AgentFocusChangedEvent(target_id=fallback_target_id, url='about:blank')
					)
					return

			# Complete failure - this should never happen
			self.logger.critical(
				'[SessionManager] 🚨 CRITICAL: Failed to recover agent_focus even with fallback! Agent may be in broken state.'
			)

		except Exception as e:
			self.logger.error(f'[SessionManager] ❌ Error during agent_focus recovery: {type(e).__name__}: {e}')
		finally:
			# Always signal completion and reset recovery state
			# This allows all waiting operations to proceed (success or failure)
			if self._recovery_complete_event:
				self._recovery_complete_event.set()
			self._recovery_in_progress = False
			self._recovery_task = None
			self.logger.debug('[SessionManager] Recovery state reset')