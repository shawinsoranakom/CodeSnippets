def run_main_interface(ctx: click.Context, debug: bool = False, **kwargs):
	"""Run the main browser-use interface"""

	if kwargs['version']:
		from importlib.metadata import version

		print(version('browser-use'))
		sys.exit(0)

	# Check if MCP server mode is activated
	if kwargs.get('mcp'):
		# Capture telemetry for MCP server mode via CLI (suppress any logging from this)
		try:
			telemetry = ProductTelemetry()
			telemetry.capture(
				CLITelemetryEvent(
					version=get_browser_use_version(),
					action='start',
					mode='mcp_server',
				)
			)
		except Exception:
			# Ignore telemetry errors in MCP mode to prevent any stdout contamination
			pass
		# Run as MCP server
		from browser_use.mcp.server import main as mcp_main

		asyncio.run(mcp_main())
		return

	# Check if prompt mode is activated
	if kwargs.get('prompt'):
		# Set environment variable for prompt mode before running
		os.environ['BROWSER_USE_LOGGING_LEVEL'] = 'result'
		# Run in non-interactive mode
		asyncio.run(run_prompt_mode(kwargs['prompt'], ctx, debug))
		return

	# Configure console logging
	console_handler = logging.StreamHandler(sys.stdout)
	console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%H:%M:%S'))

	# Configure root logger
	root_logger = logging.getLogger()
	root_logger.setLevel(logging.INFO if not debug else logging.DEBUG)
	root_logger.addHandler(console_handler)

	logger = logging.getLogger('browser_use.startup')
	logger.info('Starting Browser-Use initialization')
	if debug:
		logger.debug(f'System info: Python {sys.version.split()[0]}, Platform: {sys.platform}')

	logger.debug('Loading environment variables from .env file...')
	load_dotenv()
	logger.debug('Environment variables loaded')

	# Load user configuration
	logger.debug('Loading user configuration...')
	try:
		config = load_user_config()
		logger.debug(f'User configuration loaded from {CONFIG.BROWSER_USE_CONFIG_FILE}')
	except Exception as e:
		logger.error(f'Error loading user configuration: {str(e)}', exc_info=True)
		print(f'Error loading configuration: {str(e)}')
		sys.exit(1)

	# Update config with command-line arguments
	logger.debug('Updating configuration with command line arguments...')
	try:
		config = update_config_with_click_args(config, ctx)
		logger.debug('Configuration updated')
	except Exception as e:
		logger.error(f'Error updating config with command line args: {str(e)}', exc_info=True)
		print(f'Error updating configuration: {str(e)}')
		sys.exit(1)

	# Save updated config
	logger.debug('Saving user configuration...')
	try:
		save_user_config(config)
		logger.debug('Configuration saved')
	except Exception as e:
		logger.error(f'Error saving user configuration: {str(e)}', exc_info=True)
		print(f'Error saving configuration: {str(e)}')
		sys.exit(1)

	# Setup handlers for console output before entering Textual UI
	logger.debug('Setting up handlers for Textual UI...')

	# Log browser and model configuration that will be used
	browser_type = 'Chromium'  # BrowserSession only supports Chromium
	model_name = config.get('model', {}).get('name', 'auto-detected')
	headless = config.get('browser', {}).get('headless', False)
	headless_str = 'headless' if headless else 'visible'

	logger.info(f'Preparing {browser_type} browser ({headless_str}) with {model_name} LLM')

	try:
		# Run the Textual UI interface - now all the initialization happens before we go fullscreen
		logger.debug('Starting Textual UI interface...')
		asyncio.run(textual_interface(config))
	except Exception as e:
		# Restore console logging for error reporting
		root_logger.setLevel(logging.INFO)
		for handler in root_logger.handlers:
			root_logger.removeHandler(handler)
		root_logger.addHandler(console_handler)

		logger.error(f'Error initializing Browser-Use: {str(e)}', exc_info=debug)
		print(f'\nError launching Browser-Use: {str(e)}')
		if debug:
			import traceback

			traceback.print_exc()
		sys.exit(1)