def setup_richlog_logging(self) -> None:
		"""Set up logging to redirect to RichLog widget instead of stdout."""
		# Try to add RESULT level if it doesn't exist
		try:
			addLoggingLevel('RESULT', 35)
		except AttributeError:
			pass  # Level already exists, which is fine

		# Get the main output RichLog widget
		rich_log = self.query_one('#main-output-log', RichLog)

		# Create and set up the custom handler
		log_handler = RichLogHandler(rich_log)
		log_type = os.getenv('BROWSER_USE_LOGGING_LEVEL', 'result').lower()

		class BrowserUseFormatter(logging.Formatter):
			def format(self, record):
				# if isinstance(record.name, str) and record.name.startswith('browser_use.'):
				# 	record.name = record.name.split('.')[-2]
				return super().format(record)

		# Set up the formatter based on log type
		if log_type == 'result':
			log_handler.setLevel('RESULT')
			log_handler.setFormatter(BrowserUseFormatter('%(message)s'))
		else:
			log_handler.setFormatter(BrowserUseFormatter('%(levelname)-8s [%(name)s] %(message)s'))

		# Configure root logger - Replace ALL handlers, not just stdout handlers
		root = logging.getLogger()

		# Clear all existing handlers to prevent output to stdout/stderr
		root.handlers = []
		root.addHandler(log_handler)

		# Set log level based on environment variable
		if log_type == 'result':
			root.setLevel('RESULT')
		elif log_type == 'debug':
			root.setLevel(logging.DEBUG)
		else:
			root.setLevel(logging.INFO)

		# Configure browser_use logger and all its sub-loggers
		browser_use_logger = logging.getLogger('browser_use')
		browser_use_logger.propagate = False  # Don't propagate to root logger
		browser_use_logger.handlers = [log_handler]  # Replace any existing handlers
		browser_use_logger.setLevel(root.level)

		# Also ensure agent loggers go to the main output
		# Use a wildcard pattern to catch all agent-related loggers
		for logger_name in ['browser_use.Agent', 'browser_use.controller', 'browser_use.agent', 'browser_use.agent.service']:
			agent_logger = logging.getLogger(logger_name)
			agent_logger.propagate = False
			agent_logger.handlers = [log_handler]
			agent_logger.setLevel(root.level)

		# Also catch any dynamically created agent loggers with task IDs
		for name, logger in logging.Logger.manager.loggerDict.items():
			if isinstance(name, str) and 'browser_use.Agent' in name:
				if isinstance(logger, logging.Logger):
					logger.propagate = False
					logger.handlers = [log_handler]
					logger.setLevel(root.level)

		# Silence third-party loggers but keep them using our handler
		for logger_name in [
			'WDM',
			'httpx',
			'selenium',
			'playwright',
			'urllib3',
			'asyncio',
			'openai',
			'httpcore',
			'charset_normalizer',
			'anthropic._base_client',
			'PIL.PngImagePlugin',
			'trafilatura.htmlprocessing',
			'trafilatura',
			'groq',
		]:
			third_party = logging.getLogger(logger_name)
			third_party.setLevel(logging.ERROR)
			third_party.propagate = False
			third_party.handlers = [log_handler]