def setup_logging(stream=None, log_level=None, force_setup=False, debug_log_file=None, info_log_file=None):
	"""Setup logging configuration for browser-use.

	Args:
		stream: Output stream for logs (default: sys.stdout). Can be sys.stderr for MCP mode.
		log_level: Override log level (default: uses CONFIG.BROWSER_USE_LOGGING_LEVEL)
		force_setup: Force reconfiguration even if handlers already exist
		debug_log_file: Path to log file for debug level logs only
		info_log_file: Path to log file for info level logs only
	"""
	# Try to add RESULT level, but ignore if it already exists
	try:
		addLoggingLevel('RESULT', 35)  # This allows ERROR, FATAL and CRITICAL
	except AttributeError:
		pass  # Level already exists, which is fine

	log_type = log_level or CONFIG.BROWSER_USE_LOGGING_LEVEL

	# Check if handlers are already set up
	if logging.getLogger().hasHandlers() and not force_setup:
		return logging.getLogger('browser_use')

	# Clear existing handlers
	root = logging.getLogger()
	root.handlers = []

	class BrowserUseFormatter(logging.Formatter):
		def __init__(self, fmt, log_level):
			super().__init__(fmt)
			self.log_level = log_level

		def format(self, record):
			# Only clean up names in INFO mode, keep everything in DEBUG mode
			if self.log_level > logging.DEBUG and isinstance(record.name, str) and record.name.startswith('browser_use.'):
				# Extract clean component names from logger names
				if 'Agent' in record.name:
					record.name = 'Agent'
				elif 'BrowserSession' in record.name:
					record.name = 'BrowserSession'
				elif 'tools' in record.name:
					record.name = 'tools'
				elif 'dom' in record.name:
					record.name = 'dom'
				elif record.name.startswith('browser_use.'):
					# For other browser_use modules, use the last part
					parts = record.name.split('.')
					if len(parts) >= 2:
						record.name = parts[-1]
			return super().format(record)

	# Setup single handler for all loggers
	console = logging.StreamHandler(stream or sys.stderr)

	# Determine the log level to use first
	if log_type == 'result':
		log_level = 35  # RESULT level value
	elif log_type == 'debug':
		log_level = logging.DEBUG
	else:
		log_level = logging.INFO

	# adittional setLevel here to filter logs
	if log_type == 'result':
		console.setLevel('RESULT')
		console.setFormatter(BrowserUseFormatter('%(message)s', log_level))
	else:
		console.setLevel(log_level)  # Keep console at original log level (e.g., INFO)
		console.setFormatter(BrowserUseFormatter('%(levelname)-8s [%(name)s] %(message)s', log_level))

	# Configure root logger only
	root.addHandler(console)

	# Add file handlers if specified
	file_handlers = []

	# Create debug log file handler
	if debug_log_file:
		debug_handler = logging.FileHandler(debug_log_file, encoding='utf-8')
		debug_handler.setLevel(logging.DEBUG)
		debug_handler.setFormatter(BrowserUseFormatter('%(asctime)s - %(levelname)-8s [%(name)s] %(message)s', logging.DEBUG))
		file_handlers.append(debug_handler)
		root.addHandler(debug_handler)

	# Create info log file handler
	if info_log_file:
		info_handler = logging.FileHandler(info_log_file, encoding='utf-8')
		info_handler.setLevel(logging.INFO)
		info_handler.setFormatter(BrowserUseFormatter('%(asctime)s - %(levelname)-8s [%(name)s] %(message)s', logging.INFO))
		file_handlers.append(info_handler)
		root.addHandler(info_handler)

	# Configure root logger - use DEBUG if debug file logging is enabled
	effective_log_level = logging.DEBUG if debug_log_file else log_level
	root.setLevel(effective_log_level)

	# Configure browser_use logger
	browser_use_logger = logging.getLogger('browser_use')
	browser_use_logger.propagate = False  # Don't propagate to root logger
	browser_use_logger.addHandler(console)
	for handler in file_handlers:
		browser_use_logger.addHandler(handler)
	browser_use_logger.setLevel(effective_log_level)

	# Configure bubus logger to allow INFO level logs
	bubus_logger = logging.getLogger('bubus')
	bubus_logger.propagate = False  # Don't propagate to root logger
	bubus_logger.addHandler(console)
	for handler in file_handlers:
		bubus_logger.addHandler(handler)
	bubus_logger.setLevel(logging.INFO if log_type == 'result' else effective_log_level)

	# Configure CDP logging using cdp_use's setup function
	# This enables the formatted CDP output using CDP_LOGGING_LEVEL environment variable
	# Convert CDP_LOGGING_LEVEL string to logging level
	cdp_level_str = CONFIG.CDP_LOGGING_LEVEL.upper()
	cdp_level = getattr(logging, cdp_level_str, logging.WARNING)

	try:
		from cdp_use.logging import setup_cdp_logging  # type: ignore

		# Use the CDP-specific logging level
		setup_cdp_logging(
			level=cdp_level,
			stream=stream or sys.stderr,
			format_string='%(levelname)-8s [%(name)s] %(message)s' if log_type != 'result' else '%(message)s',
		)
	except ImportError:
		# If cdp_use doesn't have the new logging module, fall back to manual config
		cdp_loggers = [
			'websockets.client',
			'cdp_use',
			'cdp_use.client',
			'cdp_use.cdp',
			'cdp_use.cdp.registry',
		]
		for logger_name in cdp_loggers:
			cdp_logger = logging.getLogger(logger_name)
			cdp_logger.setLevel(cdp_level)
			cdp_logger.addHandler(console)
			cdp_logger.propagate = False

	logger = logging.getLogger('browser_use')
	# logger.debug('BrowserUse logging setup complete with level %s', log_type)

	# Silence third-party loggers (but not CDP ones which we configured above)
	third_party_loggers = [
		'WDM',
		'httpx',
		'selenium',
		'playwright',
		'urllib3',
		'asyncio',
		'langsmith',
		'langsmith.client',
		'openai',
		'httpcore',
		'charset_normalizer',
		'anthropic._base_client',
		'PIL.PngImagePlugin',
		'trafilatura.htmlprocessing',
		'trafilatura',
		'groq',
		'google_genai',
		'websockets',  # General websockets (but not websockets.client which we need)
	]
	for logger_name in third_party_loggers:
		third_party = logging.getLogger(logger_name)
		third_party.setLevel(logging.ERROR)
		third_party.propagate = False

	return logger