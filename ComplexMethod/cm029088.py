def on_mount(self) -> None:
		"""Set up components when app is mounted."""
		# We'll use a file logger since stdout is now controlled by Textual
		logger = logging.getLogger('browser_use.on_mount')
		logger.debug('on_mount() method started')

		# Step 1: Set up custom logging to RichLog
		logger.debug('Setting up RichLog logging...')
		try:
			self.setup_richlog_logging()
			logger.debug('RichLog logging set up successfully')
		except Exception as e:
			logger.error(f'Error setting up RichLog logging: {str(e)}', exc_info=True)
			raise RuntimeError(f'Failed to set up RichLog logging: {str(e)}')

		# Step 2: Set up input history
		logger.debug('Setting up readline history...')
		try:
			if READLINE_AVAILABLE and self.task_history and _add_history:
				for item in self.task_history:
					_add_history(item)
				logger.debug(f'Added {len(self.task_history)} items to readline history')
			else:
				logger.debug('No readline history to set up')
		except Exception as e:
			logger.error(f'Error setting up readline history: {str(e)}', exc_info=False)
			# Non-critical, continue

		# Step 3: Focus the input field
		logger.debug('Focusing input field...')
		try:
			input_field = self.query_one('#task-input', Input)
			input_field.focus()
			logger.debug('Input field focused')
		except Exception as e:
			logger.error(f'Error focusing input field: {str(e)}', exc_info=True)
			# Non-critical, continue

		# Step 5: Setup CDP logger and event bus listener if browser session is available
		logger.debug('Setting up CDP logging and event bus listener...')
		try:
			self.setup_cdp_logger()
			if self.browser_session:
				self.setup_event_bus_listener()
			logger.debug('CDP logging and event bus setup complete')
		except Exception as e:
			logger.error(f'Error setting up CDP logging/event bus: {str(e)}', exc_info=True)
			# Non-critical, continue

		# Capture telemetry for CLI start
		self._telemetry.capture(
			CLITelemetryEvent(
				version=get_browser_use_version(),
				action='start',
				mode='interactive',
				model=self.llm.model if self.llm and hasattr(self.llm, 'model') else None,
				model_provider=self.llm.provider if self.llm and hasattr(self.llm, 'provider') else None,
			)
		)

		logger.debug('on_mount() completed successfully')