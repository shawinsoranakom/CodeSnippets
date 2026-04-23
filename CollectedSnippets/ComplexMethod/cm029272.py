def __del__(self) -> None:
		"""Clean up any running tasks during garbage collection."""

		# A BIT OF MAGIC: Cancel any private attributes that look like asyncio tasks
		try:
			for attr_name in dir(self):
				# e.g. _browser_crash_watcher_task = asyncio.Task
				if attr_name.startswith('_') and attr_name.endswith('_task'):
					try:
						task = getattr(self, attr_name)
						if hasattr(task, 'cancel') and callable(task.cancel) and not task.done():
							task.cancel()
							# self.logger.debug(f'[{self.__class__.__name__}] Cancelled {attr_name} during cleanup')
					except Exception:
						pass  # Ignore errors during cleanup

				# e.g. _cdp_download_tasks = WeakSet[asyncio.Task] or list[asyncio.Task]
				if attr_name.startswith('_') and attr_name.endswith('_tasks') and isinstance(getattr(self, attr_name), Iterable):
					for task in getattr(self, attr_name):
						try:
							if hasattr(task, 'cancel') and callable(task.cancel) and not task.done():
								task.cancel()
								# self.logger.debug(f'[{self.__class__.__name__}] Cancelled {attr_name} during cleanup')
						except Exception:
							pass  # Ignore errors during cleanup
		except Exception as e:
			from browser_use.utils import logger

			logger.error(f'⚠️ Error during BrowserSession {self.__class__.__name__} garbage collection __del__(): {type(e)}: {e}')