async def handle_dialog(event_data, session_id: str | None = None):
				"""Handle JavaScript dialog events - accept immediately."""
				try:
					dialog_type = event_data.get('type', 'alert')
					message = event_data.get('message', '')

					# Store the popup message in browser session for inclusion in browser state
					if message:
						formatted_message = f'[{dialog_type}] {message}'
						self.browser_session._closed_popup_messages.append(formatted_message)
						self.logger.debug(f'📝 Stored popup message: {formatted_message[:100]}')

					# Choose action based on dialog type:
					# - alert: accept=true (click OK to dismiss)
					# - confirm: accept=true (click OK to proceed - safer for automation)
					# - prompt: accept=false (click Cancel since we can't provide input)
					# - beforeunload: accept=true (allow navigation)
					should_accept = dialog_type in ('alert', 'confirm', 'beforeunload')

					action_str = 'accepting (OK)' if should_accept else 'dismissing (Cancel)'
					self.logger.info(f"🔔 JavaScript {dialog_type} dialog: '{message[:100]}' - {action_str}...")

					dismissed = False

					# Approach 1: Use the session that detected the dialog (most reliable)
					if self.browser_session._cdp_client_root and session_id:
						try:
							self.logger.debug(f'🔄 Approach 1: Using detecting session {session_id[-8:]}')
							await asyncio.wait_for(
								self.browser_session._cdp_client_root.send.Page.handleJavaScriptDialog(
									params={'accept': should_accept},
									session_id=session_id,
								),
								timeout=0.5,
							)
							dismissed = True
							self.logger.info('✅ Dialog handled successfully via detecting session')
						except (TimeoutError, Exception) as e:
							self.logger.debug(f'Approach 1 failed: {type(e).__name__}')

					# Approach 2: Try with current agent focus session
					if not dismissed and self.browser_session._cdp_client_root and self.browser_session.agent_focus_target_id:
						try:
							# Use public API with focus=False to avoid changing focus during popup dismissal
							cdp_session = await self.browser_session.get_or_create_cdp_session(
								self.browser_session.agent_focus_target_id, focus=False
							)
							self.logger.debug(f'🔄 Approach 2: Using agent focus session {cdp_session.session_id[-8:]}')
							await asyncio.wait_for(
								self.browser_session._cdp_client_root.send.Page.handleJavaScriptDialog(
									params={'accept': should_accept},
									session_id=cdp_session.session_id,
								),
								timeout=0.5,
							)
							dismissed = True
							self.logger.info('✅ Dialog handled successfully via agent focus session')
						except (TimeoutError, Exception) as e:
							self.logger.debug(f'Approach 2 failed: {type(e).__name__}')

				except Exception as e:
					self.logger.error(f'❌ Critical error in dialog handler: {type(e).__name__}: {e}')