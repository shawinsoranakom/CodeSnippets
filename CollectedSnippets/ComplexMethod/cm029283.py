async def on_NavigateToUrlEvent(self, event: NavigateToUrlEvent) -> None:
		"""Handle navigation requests - core browser functionality."""
		self.logger.debug(f'[on_NavigateToUrlEvent] Received NavigateToUrlEvent: url={event.url}, new_tab={event.new_tab}')
		if not self.agent_focus_target_id:
			self.logger.warning('Cannot navigate - browser not connected')
			return

		target_id = None
		current_target_id = self.agent_focus_target_id

		# If new_tab=True but we're already in a new tab, set new_tab=False
		current_target = self.session_manager.get_target(current_target_id)
		if event.new_tab and is_new_tab_page(current_target.url):
			self.logger.debug(f'[on_NavigateToUrlEvent] Already on blank tab ({current_target.url}), reusing')
			event.new_tab = False

		try:
			# Find or create target for navigation
			self.logger.debug(f'[on_NavigateToUrlEvent] Processing new_tab={event.new_tab}')

			if event.new_tab:
				page_targets = self.session_manager.get_all_page_targets()
				self.logger.debug(f'[on_NavigateToUrlEvent] Found {len(page_targets)} existing tabs')

				# Look for existing about:blank tab that's not the current one
				for idx, target in enumerate(page_targets):
					self.logger.debug(f'[on_NavigateToUrlEvent] Tab {idx}: url={target.url}, targetId={target.target_id}')
					if target.url == 'about:blank' and target.target_id != current_target_id:
						target_id = target.target_id
						self.logger.debug(f'Reusing existing about:blank tab #{target_id[-4:]}')
						break

				# Create new tab if no reusable one found
				if not target_id:
					self.logger.debug('[on_NavigateToUrlEvent] No reusable about:blank tab found, creating new tab...')
					try:
						target_id = await self._cdp_create_new_page('about:blank')
						self.logger.debug(f'Created new tab #{target_id[-4:]}')
						# Dispatch TabCreatedEvent for new tab
						await self.event_bus.dispatch(TabCreatedEvent(target_id=target_id, url='about:blank'))
					except Exception as e:
						self.logger.error(f'[on_NavigateToUrlEvent] Failed to create new tab: {type(e).__name__}: {e}')
						# Fall back to using current tab
						target_id = current_target_id
						self.logger.warning(f'[on_NavigateToUrlEvent] Falling back to current tab #{target_id[-4:]}')
			else:
				# Use current tab
				target_id = target_id or current_target_id

			# Switch to target tab if needed (for both new_tab=True and new_tab=False)
			if self.agent_focus_target_id is None or self.agent_focus_target_id != target_id:
				self.logger.debug(
					f'[on_NavigateToUrlEvent] Switching to target tab {target_id[-4:]} (current: {self.agent_focus_target_id[-4:] if self.agent_focus_target_id else "none"})'
				)
				# Activate target (bring to foreground)
				await self.event_bus.dispatch(SwitchTabEvent(target_id=target_id))
			else:
				self.logger.debug(f'[on_NavigateToUrlEvent] Already on target tab {target_id[-4:]}, skipping SwitchTabEvent')

			assert self.agent_focus_target_id is not None and self.agent_focus_target_id == target_id, (
				'Agent focus not updated to new target_id after SwitchTabEvent should have switched to it'
			)

			# Dispatch navigation started
			await self.event_bus.dispatch(NavigationStartedEvent(target_id=target_id, url=event.url))

			# Navigate to URL with proper lifecycle waiting
			await self._navigate_and_wait(
				event.url,
				target_id,
				timeout=event.timeout_ms / 1000 if event.timeout_ms is not None else None,
				wait_until=event.wait_until,
				nav_timeout=event.event_timeout,
			)

			# Close any extension options pages that might have opened
			await self._close_extension_options_pages()

			# Dispatch navigation complete
			self.logger.debug(f'Dispatching NavigationCompleteEvent for {event.url} (tab #{target_id[-4:]})')
			await self.event_bus.dispatch(
				NavigationCompleteEvent(
					target_id=target_id,
					url=event.url,
					status=None,  # CDP doesn't provide status directly
				)
			)
			await self.event_bus.dispatch(AgentFocusChangedEvent(target_id=target_id, url=event.url))

			# Note: These should be handled by dedicated watchdogs:
			# - Security checks (security_watchdog)
			# - Page health checks (crash_watchdog)
			# - Dialog handling (dialog_watchdog)
			# - Download handling (downloads_watchdog)
			# - DOM rebuilding (dom_watchdog)

		except Exception as e:
			self.logger.error(f'Navigation failed: {type(e).__name__}: {e}')
			# target_id might be unbound if exception happens early
			if 'target_id' in locals() and target_id:
				await self.event_bus.dispatch(
					NavigationCompleteEvent(
						target_id=target_id,
						url=event.url,
						error_message=f'{type(e).__name__}: {e}',
					)
				)
				await self.event_bus.dispatch(AgentFocusChangedEvent(target_id=target_id, url=event.url))
			raise