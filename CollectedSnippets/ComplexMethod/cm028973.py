async def run_single_task(task_file):
	"""Run a single task in the current process (called by subprocess)"""
	try:
		print(f'[DEBUG] Starting task: {os.path.basename(task_file)}', file=sys.stderr)

		# Suppress all logging in subprocess to avoid interfering with JSON output
		logging.getLogger().setLevel(logging.CRITICAL)
		for logger_name in ['browser_use', 'telemetry', 'message_manager']:
			logging.getLogger(logger_name).setLevel(logging.CRITICAL)
		warnings.filterwarnings('ignore')

		print('[DEBUG] Loading task file...', file=sys.stderr)
		content = await anyio.Path(task_file).read_text()
		task_data = yaml.safe_load(content)
		task = task_data['task']
		judge_context = task_data.get('judge_context', ['The agent must solve the task'])
		max_steps = task_data.get('max_steps', 15)

		print(f'[DEBUG] Task: {task[:100]}...', file=sys.stderr)
		print(f'[DEBUG] Max steps: {max_steps}', file=sys.stderr)
		api_key = os.getenv('BROWSER_USE_API_KEY')
		if not api_key:
			print('[SKIP] BROWSER_USE_API_KEY is not set - skipping task evaluation', file=sys.stderr)
			return {
				'file': os.path.basename(task_file),
				'success': True,  # Mark as success so it doesn't fail CI
				'explanation': 'Skipped - API key not available (fork PR or missing secret)',
			}

		agent_llm = ChatBrowserUse(api_key=api_key)

		# Check if Google API key is available for judge LLM
		google_api_key = os.getenv('GOOGLE_API_KEY')
		if not google_api_key:
			print('[SKIP] GOOGLE_API_KEY is not set - skipping task evaluation', file=sys.stderr)
			return {
				'file': os.path.basename(task_file),
				'success': True,  # Mark as success so it doesn't fail CI
				'explanation': 'Skipped - Google API key not available (fork PR or missing secret)',
			}

		judge_llm = ChatGoogle(model='gemini-flash-lite-latest')
		print('[DEBUG] LLMs initialized', file=sys.stderr)

		# Each subprocess gets its own profile and session
		print('[DEBUG] Creating browser session...', file=sys.stderr)
		profile = BrowserProfile(
			headless=True,
			user_data_dir=None,
			chromium_sandbox=False,  # Disable sandbox for CI environment (GitHub Actions)
		)
		session = BrowserSession(browser_profile=profile)
		print('[DEBUG] Browser session created', file=sys.stderr)

		# Test if browser is working
		try:
			await session.start()
			from browser_use.browser.events import NavigateToUrlEvent

			event = session.event_bus.dispatch(NavigateToUrlEvent(url='https://httpbin.org/get', new_tab=True))
			await event
			print('[DEBUG] Browser test: navigation successful', file=sys.stderr)
			title = await session.get_current_page_title()
			print(f"[DEBUG] Browser test: got title '{title}'", file=sys.stderr)
		except Exception as browser_error:
			print(f'[DEBUG] Browser test failed: {str(browser_error)}', file=sys.stderr)
			print(
				f'[DEBUG] Browser error type: {type(browser_error).__name__}',
				file=sys.stderr,
			)

		print('[DEBUG] Starting agent execution...', file=sys.stderr)
		agent = Agent(task=task, llm=agent_llm, browser_session=session)

		try:
			history: AgentHistoryList = await agent.run(max_steps=max_steps)
			print('[DEBUG] Agent.run() returned successfully', file=sys.stderr)
		except Exception as agent_error:
			print(
				f'[DEBUG] Agent.run() failed with error: {str(agent_error)}',
				file=sys.stderr,
			)
			print(f'[DEBUG] Error type: {type(agent_error).__name__}', file=sys.stderr)
			# Re-raise to be caught by outer try-catch
			raise agent_error

		agent_output = history.final_result() or ''
		print('[DEBUG] Agent execution completed', file=sys.stderr)

		# Test if LLM is working by making a simple call
		try:
			response = await agent_llm.ainvoke([UserMessage(content="Say 'test'")])
			print(
				f'[DEBUG] LLM test call successful: {response.completion[:50]}',
				file=sys.stderr,
			)
		except Exception as llm_error:
			print(f'[DEBUG] LLM test call failed: {str(llm_error)}', file=sys.stderr)

		# Debug: capture more details about the agent execution
		total_steps = len(history.history) if hasattr(history, 'history') else 0
		last_action = history.history[-1] if hasattr(history, 'history') and history.history else None
		debug_info = f'Steps: {total_steps}, Final result length: {len(agent_output)}'
		if last_action:
			debug_info += f', Last action: {type(last_action).__name__}'

		# Log to stderr so it shows up in GitHub Actions (won't interfere with JSON output to stdout)
		print(f'[DEBUG] Task {os.path.basename(task_file)}: {debug_info}', file=sys.stderr)
		if agent_output:
			print(
				f'[DEBUG] Agent output preview: {agent_output[:200]}...',
				file=sys.stderr,
			)
		else:
			print('[DEBUG] Agent produced no output!', file=sys.stderr)

		criteria = '\n- '.join(judge_context)
		judge_prompt = f"""
You are a evaluator of a browser agent task inside a ci/cd pipeline. Here was the agent's task:
{task}

Here is the agent's output:
{agent_output if agent_output else '[No output provided]'}

Debug info: {debug_info}

Criteria for success:
- {criteria}

Reply in JSON with keys: success (true/false), explanation (string).
If the agent provided no output, explain what might have gone wrong.
"""
		response = await judge_llm.ainvoke([UserMessage(content=judge_prompt)], output_format=JudgeResponse)
		judge_response = response.completion

		result = {
			'file': os.path.basename(task_file),
			'success': judge_response.success,
			'explanation': judge_response.explanation,
		}

		# Clean up session before returning
		await session.kill()

		return result

	except Exception as e:
		# Ensure session cleanup even on error
		try:
			await session.kill()
		except Exception:
			pass

		return {
			'file': os.path.basename(task_file),
			'success': False,
			'explanation': f'Task failed with error: {str(e)}',
		}