async def agent_task_worker() -> None:
			logger.debug('\n🚀 Working on task: %s', task)

			# Set flags to indicate the agent is running
			if self.agent:
				self.agent.running = True  # type: ignore
				self.agent.last_response_time = 0  # type: ignore

			# Panel updates are already happening via the timer in update_info_panels

			task_start_time = time.time()
			error_msg = None

			try:
				# Capture telemetry for message sent
				self._telemetry.capture(
					CLITelemetryEvent(
						version=get_browser_use_version(),
						action='message_sent',
						mode='interactive',
						model=self.llm.model if self.llm and hasattr(self.llm, 'model') else None,
						model_provider=self.llm.provider if self.llm and hasattr(self.llm, 'provider') else None,
					)
				)

				# Run the agent task, redirecting output to RichLog through our handler
				if self.agent:
					await self.agent.run()
			except Exception as e:
				error_msg = str(e)
				logger.error('\nError running agent: %s', str(e))
			finally:
				# Clear the running flag
				if self.agent:
					self.agent.running = False  # type: ignore

				# Capture telemetry for task completion
				duration = time.time() - task_start_time
				self._telemetry.capture(
					CLITelemetryEvent(
						version=get_browser_use_version(),
						action='task_completed' if error_msg is None else 'error',
						mode='interactive',
						model=self.llm.model if self.llm and hasattr(self.llm, 'model') else None,
						model_provider=self.llm.provider if self.llm and hasattr(self.llm, 'provider') else None,
						duration_seconds=duration,
						error_message=error_msg,
					)
				)

				logger.debug('\n✅ Task completed!')

				# Make sure the task input container is visible
				task_input_container = self.query_one('#task-input-container')
				task_input_container.display = True

				# Refocus the input field
				input_field = self.query_one('#task-input', Input)
				input_field.focus()

				# Ensure the input is visible by scrolling to it
				self.call_after_refresh(self.scroll_to_input)