async def textual_interface(config: dict[str, Any]):
	"""Run the Textual interface."""
	# Prevent browser_use from setting up logging at import time
	os.environ['BROWSER_USE_SETUP_LOGGING'] = 'false'

	logger = logging.getLogger('browser_use.startup')

	# Set up logging for Textual UI - prevent any logging to stdout
	def setup_textual_logging():
		# Replace all handlers with null handler
		root_logger = logging.getLogger()
		for handler in root_logger.handlers:
			root_logger.removeHandler(handler)

		# Add null handler to ensure no output to stdout/stderr
		null_handler = logging.NullHandler()
		root_logger.addHandler(null_handler)
		logger.debug('Logging configured for Textual UI')

	logger.debug('Setting up Browser, Controller, and LLM...')

	# Step 1: Initialize BrowserSession with config
	logger.debug('Initializing BrowserSession...')
	try:
		# Get browser config from the config dict
		browser_config = config.get('browser', {})

		logger.info('Browser type: chromium')  # BrowserSession only supports chromium
		if browser_config.get('executable_path'):
			logger.info(f'Browser binary: {browser_config["executable_path"]}')
		if browser_config.get('headless'):
			logger.info('Browser mode: headless')
		else:
			logger.info('Browser mode: visible')

		# Create BrowserSession directly with config parameters
		# Remove None values from browser_config
		browser_config = {k: v for k, v in browser_config.items() if v is not None}
		# Create BrowserProfile with user_data_dir
		profile = BrowserProfile(user_data_dir=str(USER_DATA_DIR), **browser_config)
		browser_session = BrowserSession(
			browser_profile=profile,
		)
		logger.debug('BrowserSession initialized successfully')

		# Set up FIFO logging pipes for streaming logs to UI
		try:
			from browser_use.logging_config import setup_log_pipes

			setup_log_pipes(session_id=browser_session.id)
			logger.debug(f'FIFO logging pipes set up for session {browser_session.id[-4:]}')
		except Exception as e:
			logger.debug(f'Could not set up FIFO logging pipes: {e}')

		# Browser version logging not available with CDP implementation
	except Exception as e:
		logger.error(f'Error initializing BrowserSession: {str(e)}', exc_info=True)
		raise RuntimeError(f'Failed to initialize BrowserSession: {str(e)}')

	# Step 3: Initialize Controller
	logger.debug('Initializing Controller...')
	try:
		controller = Controller()
		logger.debug('Controller initialized successfully')
	except Exception as e:
		logger.error(f'Error initializing Controller: {str(e)}', exc_info=True)
		raise RuntimeError(f'Failed to initialize Controller: {str(e)}')

	# Step 4: Get LLM
	logger.debug('Getting LLM...')
	try:
		# Ensure setup_logging is not called when importing modules
		os.environ['BROWSER_USE_SETUP_LOGGING'] = 'false'
		llm = get_llm(config)
		# Log LLM details
		model_name = getattr(llm, 'model_name', None) or getattr(llm, 'model', 'Unknown model')
		provider = llm.__class__.__name__
		temperature = getattr(llm, 'temperature', 0.0)
		logger.info(f'LLM: {provider} ({model_name}), temperature: {temperature}')
		logger.debug(f'LLM initialized successfully: {provider}')
	except Exception as e:
		logger.error(f'Error getting LLM: {str(e)}', exc_info=True)
		raise RuntimeError(f'Failed to initialize LLM: {str(e)}')

	logger.debug('Initializing BrowserUseApp instance...')
	try:
		app = BrowserUseApp(config)
		# Pass the initialized components to the app
		app.browser_session = browser_session
		app.controller = controller
		app.llm = llm

		# Set up event bus listener now that browser session is available
		# Note: This needs to be called before run_async() but after browser_session is set
		# We'll defer this to on_mount() since it needs the widgets to be available

		# Configure logging for Textual UI before going fullscreen
		setup_textual_logging()

		# Log browser and model configuration that will be used
		browser_type = 'Chromium'  # BrowserSession only supports Chromium
		model_name = config.get('model', {}).get('name', 'auto-detected')
		headless = config.get('browser', {}).get('headless', False)
		headless_str = 'headless' if headless else 'visible'

		logger.info(f'Preparing {browser_type} browser ({headless_str}) with {model_name} LLM')

		logger.debug('Starting Textual app with run_async()...')
		# No more logging after this point as we're in fullscreen mode
		await app.run_async()
	except Exception as e:
		logger.error(f'Error in textual_interface: {str(e)}', exc_info=True)
		# Note: We don't close the browser session here to avoid duplicate stop() calls
		# The browser session will be cleaned up by its __del__ method if needed
		raise