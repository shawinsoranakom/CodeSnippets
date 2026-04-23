def _handle_task_exception(t: asyncio.Task[T]) -> None:
		"""Callback to handle task exceptions"""
		exc_to_raise = None
		try:
			# This will raise if the task had an exception
			exc = t.exception()
			if exc is not None:
				task_name = t.get_name() if hasattr(t, 'get_name') else 'unnamed'
				if suppress_exceptions:
					log.error(f'Exception in background task [{task_name}]: {type(exc).__name__}: {exc}', exc_info=exc)
				else:
					# Log at warning level then mark for re-raising
					log.warning(
						f'Exception in background task [{task_name}]: {type(exc).__name__}: {exc}',
						exc_info=exc,
					)
					exc_to_raise = exc
		except asyncio.CancelledError:
			# Task was cancelled, this is normal behavior
			pass
		except Exception as e:
			# Catch any other exception during exception handling (e.g., t.exception() itself failing)
			task_name = t.get_name() if hasattr(t, 'get_name') else 'unnamed'
			log.error(f'Error handling exception in task [{task_name}]: {type(e).__name__}: {e}')

		# Re-raise outside the try-except block so it propagates to the event loop
		if exc_to_raise is not None:
			raise exc_to_raise