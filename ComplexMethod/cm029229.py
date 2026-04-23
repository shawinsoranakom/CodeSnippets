async def run(
		self,
		max_steps: int = 500,
		on_step_start: AgentHookFunc | None = None,
		on_step_end: AgentHookFunc | None = None,
	) -> AgentHistoryList[AgentStructuredOutput]:
		"""Execute the task with maximum number of steps"""

		loop = asyncio.get_event_loop()
		agent_run_error: str | None = None  # Initialize error tracking variable
		self._force_exit_telemetry_logged = False  # ADDED: Flag for custom telemetry on force exit
		should_delay_close = False

		# Set up the  signal handler with callbacks specific to this agent
		from browser_use.utils import SignalHandler

		# Define the custom exit callback function for second CTRL+C
		def on_force_exit_log_telemetry():
			self._log_agent_event(max_steps=max_steps, agent_run_error='SIGINT: Cancelled by user')
			# NEW: Call the flush method on the telemetry instance
			if hasattr(self, 'telemetry') and self.telemetry:
				self.telemetry.flush()
			self._force_exit_telemetry_logged = True  # Set the flag

		signal_handler = SignalHandler(
			loop=loop,
			pause_callback=self.pause,
			resume_callback=self.resume,
			custom_exit_callback=on_force_exit_log_telemetry,  # Pass the new telemetrycallback
			exit_on_second_int=True,
			disabled=not self.enable_signal_handler,
		)
		signal_handler.register()

		try:
			await self._log_agent_run()

			self.logger.debug(
				f'🔧 Agent setup: Agent Session ID {self.session_id[-4:]}, Task ID {self.task_id[-4:]}, Browser Session ID {self.browser_session.id[-4:] if self.browser_session else "None"} {"(connecting via CDP)" if (self.browser_session and self.browser_session.cdp_url) else "(launching local browser)"}'
			)

			# Initialize timing for session and task
			self._session_start_time = time.time()
			self._task_start_time = self._session_start_time  # Initialize task start time

			# Only dispatch session events if this is the first run
			if not self.state.session_initialized:
				self.logger.debug('📡 Dispatching CreateAgentSessionEvent...')
				# Emit CreateAgentSessionEvent at the START of run()
				self.eventbus.dispatch(CreateAgentSessionEvent.from_agent(self))

				self.state.session_initialized = True

			self.logger.debug('📡 Dispatching CreateAgentTaskEvent...')
			# Emit CreateAgentTaskEvent at the START of run()
			self.eventbus.dispatch(CreateAgentTaskEvent.from_agent(self))

			# Log startup message on first step (only if we haven't already done steps)
			self._log_first_step_startup()
			# Start browser session and attach watchdogs
			await self.browser_session.start()
			if self._demo_mode_enabled:
				await self._demo_mode_log(f'Started task: {self.task}', 'info', {'tag': 'task'})
				await self._demo_mode_log(
					'Demo mode active - follow the side panel for live thoughts and actions.',
					'info',
					{'tag': 'status'},
				)

			# Register skills as actions if SkillService is configured
			await self._register_skills_as_actions()

			# Normally there was no try catch here but the callback can raise an InterruptedError.
			# Wrap with step_timeout so initial actions (usually a single URL navigate) can't
			# hang indefinitely on a silent CDP WebSocket — without this the agent would take
			# zero steps and return with an empty history while any outer watchdog waits.
			try:
				await asyncio.wait_for(
					self._execute_initial_actions(),
					timeout=self.settings.step_timeout,
				)
			except InterruptedError:
				pass
			except TimeoutError:
				initial_timeout_msg = (
					f'Initial actions timed out after {self.settings.step_timeout}s '
					f'(browser may be unresponsive). Proceeding to main execution loop.'
				)
				self.logger.error(f'⏰ {initial_timeout_msg}')
				self.state.last_result = [ActionResult(error=initial_timeout_msg)]
				self.state.consecutive_failures += 1
			except Exception as e:
				raise e

			self.logger.debug(
				f'🔄 Starting main execution loop with max {max_steps} steps (currently at step {self.state.n_steps})...'
			)
			while self.state.n_steps <= max_steps:
				current_step = self.state.n_steps - 1  # Convert to 0-indexed for step_info

				# Use the consolidated pause state management
				if self.state.paused:
					self.logger.debug(f'⏸️ Step {self.state.n_steps}: Agent paused, waiting to resume...')
					await self._external_pause_event.wait()
					signal_handler.reset()

				# Check if we should stop due to too many failures, if final_response_after_failure is True, we try one last time
				if (self.state.consecutive_failures) >= self.settings.max_failures + int(
					self.settings.final_response_after_failure
				):
					self.logger.error(f'❌ Stopping due to {self.settings.max_failures} consecutive failures')
					agent_run_error = f'Stopped due to {self.settings.max_failures} consecutive failures'
					break

				# Check control flags before each step
				if self.state.stopped:
					self.logger.info('🛑 Agent stopped')
					agent_run_error = 'Agent stopped programmatically'
					break

				step_info = AgentStepInfo(step_number=current_step, max_steps=max_steps)
				is_done = await self._execute_step(current_step, max_steps, step_info, on_step_start, on_step_end)

				if is_done:
					# Agent has marked the task as done
					if self._demo_mode_enabled and self.history.history:
						final_result_text = self.history.final_result() or 'Task completed'
						await self._demo_mode_log(f'Final Result: {final_result_text}', 'success', {'tag': 'task'})

					should_delay_close = True
					break
			else:
				agent_run_error = 'Failed to complete task in maximum steps'

				self.history.add_item(
					AgentHistory(
						model_output=None,
						result=[ActionResult(error=agent_run_error, include_in_memory=True)],
						state=BrowserStateHistory(
							url='',
							title='',
							tabs=[],
							interacted_element=[],
							screenshot_path=None,
						),
						metadata=None,
					)
				)

				self.logger.info(f'❌ {agent_run_error}')

			self.history.usage = await self.token_cost_service.get_usage_summary()

			# set the model output schema and call it on the fly
			if self.history._output_model_schema is None and self.output_model_schema is not None:
				self.history._output_model_schema = self.output_model_schema

			return self.history

		except KeyboardInterrupt:
			# Already handled by our signal handler, but catch any direct KeyboardInterrupt as well
			self.logger.debug('Got KeyboardInterrupt during execution, returning current history')
			agent_run_error = 'KeyboardInterrupt'

			self.history.usage = await self.token_cost_service.get_usage_summary()

			return self.history

		except Exception as e:
			self.logger.error(f'Agent run failed with exception: {e}', exc_info=True)
			agent_run_error = str(e)
			raise e

		finally:
			if should_delay_close and self._demo_mode_enabled and agent_run_error is None:
				await asyncio.sleep(30)
			if agent_run_error:
				await self._demo_mode_log(f'Agent stopped: {agent_run_error}', 'error', {'tag': 'run'})
			# Log token usage summary
			await self.token_cost_service.log_usage_summary()

			# Unregister signal handlers before cleanup
			signal_handler.unregister()

			if not self._force_exit_telemetry_logged:  # MODIFIED: Check the flag
				try:
					self._log_agent_event(max_steps=max_steps, agent_run_error=agent_run_error)
				except Exception as log_e:  # Catch potential errors during logging itself
					self.logger.error(f'Failed to log telemetry event: {log_e}', exc_info=True)
			else:
				# ADDED: Info message when custom telemetry for SIGINT was already logged
				self.logger.debug('Telemetry for force exit (SIGINT) was logged by custom exit callback.')

			# NOTE: CreateAgentSessionEvent and CreateAgentTaskEvent are now emitted at the START of run()
			# to match backend requirements for CREATE events to be fired when entities are created,
			# not when they are completed

			# Emit UpdateAgentTaskEvent at the END of run() with final task state
			self.eventbus.dispatch(UpdateAgentTaskEvent.from_agent(self))

			# Generate GIF if needed before stopping event bus
			if self.settings.generate_gif:
				output_path: str = 'agent_history.gif'
				if isinstance(self.settings.generate_gif, str):
					output_path = self.settings.generate_gif

				# Lazy import gif module to avoid heavy startup cost
				from browser_use.agent.gif import create_history_gif

				create_history_gif(task=self.task, history=self.history, output_path=output_path)

				# Only emit output file event if GIF was actually created
				if Path(output_path).exists():
					output_event = await CreateAgentOutputFileEvent.from_agent_and_file(self, output_path)
					self.eventbus.dispatch(output_event)

			# Log final messages to user based on outcome
			self._log_final_outcome_messages()

			# Stop the event bus gracefully, waiting for all events to be processed
			# Configurable via TIMEOUT_AgentEventBusStop env var (default: 3.0s)
			await self.eventbus.stop(clear=True, timeout=_get_timeout('TIMEOUT_AgentEventBusStop', 3.0))

			await self.close()