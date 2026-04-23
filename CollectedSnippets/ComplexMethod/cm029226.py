async def take_step(self, step_info: AgentStepInfo | None = None) -> tuple[bool, bool]:
		"""Take a step

		Returns:
		        Tuple[bool, bool]: (is_done, is_valid)
		"""
		if step_info is not None and step_info.step_number == 0:
			# First step
			self._log_first_step_startup()
			# Normally there was no try catch here but the callback can raise an InterruptedError which we skip
			try:
				await self._execute_initial_actions()
			except InterruptedError:
				pass
			except Exception as e:
				raise e

		await self.step(step_info)

		if self.history.is_done():
			await self.log_completion()

			# Run full judge before done callback if enabled
			if self.settings.use_judge:
				await self._judge_and_log()

			if self.register_done_callback:
				if inspect.iscoroutinefunction(self.register_done_callback):
					await self.register_done_callback(self.history)
				else:
					self.register_done_callback(self.history)
			return True, True

		return False, False