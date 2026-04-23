async def unique_handler(event):
				# Circuit breaker: skip handler if CDP WebSocket is dead
				# (prevents handlers from hanging on broken connections until timeout)
				# Lifecycle events are exempt — they manage browser start/stop
				if event.event_type not in LIFECYCLE_EVENT_NAMES and not browser_session.is_cdp_connected:
					# If reconnection is in progress, wait for it instead of silently skipping
					if browser_session.is_reconnecting:
						wait_timeout = browser_session.RECONNECT_WAIT_TIMEOUT
						browser_session.logger.debug(
							f'🚌 [{watchdog_class_name}.{actual_handler.__name__}] ⏳ Waiting for reconnection ({wait_timeout}s)...'
						)
						try:
							await asyncio.wait_for(browser_session._reconnect_event.wait(), timeout=wait_timeout)
						except TimeoutError:
							raise ConnectionError(
								f'[{watchdog_class_name}.{actual_handler.__name__}] '
								f'Reconnection wait timed out after {wait_timeout}s'
							)
						# After wait: check if reconnection actually succeeded
						if not browser_session.is_cdp_connected:
							raise ConnectionError(
								f'[{watchdog_class_name}.{actual_handler.__name__}] Reconnection failed — CDP still not connected'
							)
						# Reconnection succeeded — fall through to execute handler normally
					else:
						# Not reconnecting — intentional stop, backward compat silent skip
						browser_session.logger.debug(
							f'🚌 [{watchdog_class_name}.{actual_handler.__name__}] ⚡ Skipped — CDP not connected'
						)
						return None

				# just for debug logging, not used for anything else
				parent_event = event_bus.event_history.get(event.event_parent_id) if event.event_parent_id else None
				grandparent_event = (
					event_bus.event_history.get(parent_event.event_parent_id)
					if parent_event and parent_event.event_parent_id
					else None
				)
				parent = (
					f'↲  triggered by on_{parent_event.event_type}#{parent_event.event_id[-4:]}'
					if parent_event
					else '👈 by Agent'
				)
				grandparent = (
					(
						f'↲  under {grandparent_event.event_type}#{grandparent_event.event_id[-4:]}'
						if grandparent_event
						else '👈 by Agent'
					)
					if parent_event
					else ''
				)
				event_str = f'#{event.event_id[-4:]}'
				time_start = time.time()
				watchdog_and_handler_str = f'[{watchdog_class_name}.{actual_handler.__name__}({event_str})]'.ljust(54)
				browser_session.logger.debug(f'🚌 {watchdog_and_handler_str} ⏳ Starting...       {parent} {grandparent}')

				try:
					# **EXECUTE THE EVENT HANDLER FUNCTION**
					result = await actual_handler(event)

					if isinstance(result, Exception):
						raise result

					# just for debug logging, not used for anything else
					time_end = time.time()
					time_elapsed = time_end - time_start
					result_summary = '' if result is None else f' ➡️ <{type(result).__name__}>'
					parents_summary = f' {parent}'.replace('↲  triggered by ', '⤴  returned to  ').replace(
						'👈 by Agent', '👉 returned to  Agent'
					)
					browser_session.logger.debug(
						f'🚌 {watchdog_and_handler_str} Succeeded ({time_elapsed:.2f}s){result_summary}{parents_summary}'
					)
					return result
				except Exception as e:
					time_end = time.time()
					time_elapsed = time_end - time_start
					original_error = e
					browser_session.logger.error(
						f'🚌 {watchdog_and_handler_str} ❌ Failed ({time_elapsed:.2f}s): {type(e).__name__}: {e}'
					)

					# attempt to repair potentially crashed CDP session
					try:
						if browser_session.agent_focus_target_id:
							# With event-driven sessions, Chrome will send detach/attach events
							# SessionManager handles pool cleanup automatically
							target_id_to_restore = browser_session.agent_focus_target_id
							browser_session.logger.debug(
								f'🚌 {watchdog_and_handler_str} ⚠️ Session error detected, waiting for CDP events to sync (target: {target_id_to_restore})'
							)

							# Wait for new attach event to restore the session
							# This will raise ValueError if target doesn't re-attach
							await browser_session.get_or_create_cdp_session(target_id=target_id_to_restore, focus=True)
						else:
							# Try to get any available session
							await browser_session.get_or_create_cdp_session(target_id=None, focus=True)
					except Exception as sub_error:
						if 'ConnectionClosedError' in str(type(sub_error)) or 'ConnectionError' in str(type(sub_error)):
							browser_session.logger.error(
								f'🚌 {watchdog_and_handler_str} ❌ Browser closed or CDP Connection disconnected by remote. {type(sub_error).__name__}: {sub_error}\n'
							)
							raise
						else:
							browser_session.logger.error(
								f'🚌 {watchdog_and_handler_str} ❌ CDP connected but failed to re-create CDP session after error "{type(original_error).__name__}: {original_error}" in {actual_handler.__name__}({event.event_type}#{event.event_id[-4:]}): due to {type(sub_error).__name__}: {sub_error}\n'
							)

					# Always re-raise the original error with its traceback preserved
					raise