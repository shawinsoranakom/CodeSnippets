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