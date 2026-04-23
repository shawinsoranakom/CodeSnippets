async def _generate_rerun_summary(
		self, original_task: str, results: list[ActionResult], summary_llm: BaseChatModel | None = None
	) -> ActionResult:
		"""Generate AI summary of rerun completion using screenshot and last step info"""
		from browser_use.agent.views import RerunSummaryAction

		# Get current screenshot
		screenshot_b64 = None
		try:
			screenshot = await self.browser_session.take_screenshot(full_page=False)
			if screenshot:
				import base64

				screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
		except Exception as e:
			self.logger.warning(f'Failed to capture screenshot for rerun summary: {e}')

		# Build summary prompt and message
		error_count = sum(1 for r in results if r.error)
		success_count = len(results) - error_count

		from browser_use.agent.prompts import get_rerun_summary_message, get_rerun_summary_prompt

		prompt = get_rerun_summary_prompt(
			original_task=original_task,
			total_steps=len(results),
			success_count=success_count,
			error_count=error_count,
		)

		# Use provided LLM, agent's LLM, or fall back to OpenAI with structured output
		try:
			# Determine which LLM to use
			if summary_llm is None:
				# Try to use the agent's LLM first
				summary_llm = self.llm
				self.logger.debug('Using agent LLM for rerun summary')
			else:
				self.logger.debug(f'Using provided LLM for rerun summary: {summary_llm.model}')

			# Build message with prompt and optional screenshot
			from browser_use.llm.messages import BaseMessage

			message = get_rerun_summary_message(prompt, screenshot_b64)
			messages: list[BaseMessage] = [message]  # type: ignore[list-item]

			# Try calling with structured output first
			self.logger.debug(f'Calling LLM for rerun summary with {len(messages)} message(s)')
			try:
				kwargs: dict = {'output_format': RerunSummaryAction}
				response = await summary_llm.ainvoke(messages, **kwargs)
				summary: RerunSummaryAction = response.completion  # type: ignore[assignment]
				self.logger.debug(f'LLM response type: {type(summary)}')
				self.logger.debug(f'LLM response: {summary}')
			except Exception as structured_error:
				# If structured output fails (e.g., Browser-Use LLM doesn't support it for this type),
				# fall back to text response without parsing
				self.logger.debug(f'Structured output failed: {structured_error}, falling back to text response')

				response = await summary_llm.ainvoke(messages, None)
				response_text = response.completion
				self.logger.debug(f'LLM text response: {response_text}')

				# Use the text response directly as the summary
				summary = RerunSummaryAction(
					summary=response_text if isinstance(response_text, str) else str(response_text),
					success=error_count == 0,
					completion_status='complete' if error_count == 0 else ('partial' if success_count > 0 else 'failed'),
				)

			self.logger.info(f'📊 Rerun Summary: {summary.summary}')
			self.logger.info(f'📊 Status: {summary.completion_status} (success={summary.success})')

			return ActionResult(
				is_done=True,
				success=summary.success,
				extracted_content=summary.summary,
				long_term_memory=f'Rerun completed with status: {summary.completion_status}. {summary.summary[:100]}',
			)

		except Exception as e:
			self.logger.warning(f'Failed to generate AI summary: {e.__class__.__name__}: {e}')
			self.logger.debug('Full error traceback:', exc_info=True)
			# Fallback to simple summary
			return ActionResult(
				is_done=True,
				success=error_count == 0,
				extracted_content=f'Rerun completed: {success_count}/{len(results)} steps succeeded',
				long_term_memory=f'Rerun completed: {success_count} steps succeeded, {error_count} errors',
			)