async def run_prompt_mode(prompt: str, ctx: click.Context, debug: bool = False):
	"""Run browser-use in non-interactive mode with a single prompt."""
	# Import and call setup_logging to ensure proper initialization
	from browser_use.logging_config import setup_logging

	# Set up logging to only show results by default
	os.environ['BROWSER_USE_LOGGING_LEVEL'] = 'result'

	# Re-run setup_logging to apply the new log level
	setup_logging()

	# The logging is now properly configured by setup_logging()
	# No need to manually configure handlers since setup_logging() handles it

	# Initialize telemetry
	telemetry = ProductTelemetry()
	start_time = time.time()
	error_msg = None

	try:
		# Load config
		config = load_user_config()
		config = update_config_with_click_args(config, ctx)

		# Get LLM
		llm = get_llm(config)

		# Capture telemetry for CLI start in oneshot mode
		telemetry.capture(
			CLITelemetryEvent(
				version=get_browser_use_version(),
				action='start',
				mode='oneshot',
				model=llm.model if hasattr(llm, 'model') else None,
				model_provider=llm.__class__.__name__ if llm else None,
			)
		)

		# Get agent settings from config
		agent_settings = AgentSettings.model_validate(config.get('agent', {}))

		# Create browser session with config parameters
		browser_config = config.get('browser', {})
		# Remove None values from browser_config
		browser_config = {k: v for k, v in browser_config.items() if v is not None}
		# Create BrowserProfile with user_data_dir
		profile = BrowserProfile(user_data_dir=str(USER_DATA_DIR), **browser_config)
		browser_session = BrowserSession(
			browser_profile=profile,
		)

		# Create and run agent
		agent = Agent(
			task=prompt,
			llm=llm,
			browser_session=browser_session,
			source='cli',
			**agent_settings.model_dump(),
		)

		await agent.run()

		# Ensure the browser session is fully stopped
		# The agent's close() method only kills the browser if keep_alive=False,
		# but we need to ensure all background tasks are stopped regardless
		if browser_session:
			try:
				# Kill the browser session to stop all background tasks
				await browser_session.kill()
			except Exception:
				# Ignore errors during cleanup
				pass

		# Capture telemetry for successful completion
		telemetry.capture(
			CLITelemetryEvent(
				version=get_browser_use_version(),
				action='task_completed',
				mode='oneshot',
				model=llm.model if hasattr(llm, 'model') else None,
				model_provider=llm.__class__.__name__ if llm else None,
				duration_seconds=time.time() - start_time,
			)
		)

	except Exception as e:
		error_msg = str(e)
		# Capture telemetry for error
		telemetry.capture(
			CLITelemetryEvent(
				version=get_browser_use_version(),
				action='error',
				mode='oneshot',
				model=llm.model if hasattr(llm, 'model') else None,
				model_provider=llm.__class__.__name__ if llm and 'llm' in locals() else None,
				duration_seconds=time.time() - start_time,
				error_message=error_msg,
			)
		)
		if debug:
			import traceback

			traceback.print_exc()
		else:
			print(f'Error: {str(e)}', file=sys.stderr)
		sys.exit(1)
	finally:
		# Ensure telemetry is flushed
		telemetry.flush()

		# Give a brief moment for cleanup to complete
		await asyncio.sleep(0.1)

		# Cancel any remaining tasks to ensure clean exit
		tasks = [t for t in asyncio.all_tasks() if t != asyncio.current_task()]
		for task in tasks:
			task.cancel()

		# Wait for all tasks to be cancelled
		if tasks:
			await asyncio.gather(*tasks, return_exceptions=True)