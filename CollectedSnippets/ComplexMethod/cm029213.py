async def _post_process(self) -> None:
		"""Handle post-action processing like download tracking and result logging"""
		assert self.browser_session is not None, 'BrowserSession is not set up'

		# Check for new downloads after executing actions
		await self._check_and_update_downloads('after executing actions')

		# Update plan state from model output
		if self.state.last_model_output is not None:
			self._update_plan_from_model_output(self.state.last_model_output)

		# Record executed actions for loop detection
		self._update_loop_detector_actions()

		# check for action errors - only count single-action steps toward consecutive failures;
		# multi-action steps with errors are handled by loop detection and replan nudges instead
		if self.state.last_result and len(self.state.last_result) == 1 and self.state.last_result[-1].error:
			self.state.consecutive_failures += 1
			self.logger.debug(f'🔄 Step {self.state.n_steps}: Consecutive failures: {self.state.consecutive_failures}')
			return

		if self.state.consecutive_failures > 0:
			self.state.consecutive_failures = 0
			self.logger.debug(f'🔄 Step {self.state.n_steps}: Consecutive failures reset to: {self.state.consecutive_failures}')

		# Log completion results
		if self.state.last_result and len(self.state.last_result) > 0 and self.state.last_result[-1].is_done:
			success = self.state.last_result[-1].success
			if success:
				# Green color for success
				self.logger.info(f'\n📄 \033[32m Final Result:\033[0m \n{self.state.last_result[-1].extracted_content}\n\n')
			else:
				# Red color for failure
				self.logger.info(f'\n📄 \033[31m Final Result:\033[0m \n{self.state.last_result[-1].extracted_content}\n\n')
			if self.state.last_result[-1].attachments:
				total_attachments = len(self.state.last_result[-1].attachments)
				for i, file_path in enumerate(self.state.last_result[-1].attachments):
					self.logger.info(f'👉 Attachment {i + 1 if total_attachments > 1 else ""}: {file_path}')