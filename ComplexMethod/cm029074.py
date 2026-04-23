def _cancel_interruptible_tasks(self) -> None:
		"""Cancel current tasks that should be interruptible."""
		current_task = asyncio.current_task(self.loop)
		for task in asyncio.all_tasks(self.loop):
			if task != current_task and not task.done():
				task_name = task.get_name() if hasattr(task, 'get_name') else str(task)
				# Cancel tasks that match certain patterns
				if any(pattern in task_name for pattern in self.interruptible_task_patterns):
					logger.debug(f'Cancelling task: {task_name}')
					task.cancel()
					# Add exception handler to silence "Task exception was never retrieved" warnings
					task.add_done_callback(lambda t: t.exception() if t.cancelled() else None)

		# Also cancel the current task if it's interruptible
		if current_task and not current_task.done():
			task_name = current_task.get_name() if hasattr(current_task, 'get_name') else str(current_task)
			if any(pattern in task_name for pattern in self.interruptible_task_patterns):
				logger.debug(f'Cancelling current task: {task_name}')
				current_task.cancel()