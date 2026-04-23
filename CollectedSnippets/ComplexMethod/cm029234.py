async def rerun_history(
		self,
		history: AgentHistoryList,
		max_retries: int = 3,
		skip_failures: bool = False,
		delay_between_actions: float = 2.0,
		max_step_interval: float = 45.0,
		summary_llm: BaseChatModel | None = None,
		ai_step_llm: BaseChatModel | None = None,
		wait_for_elements: bool = False,
	) -> list[ActionResult]:
		"""
		Rerun a saved history of actions with error handling and retry logic.

		Args:
		                history: The history to replay
		                max_retries: Maximum number of retries per action
		                skip_failures: Whether to skip failed actions or stop execution. When True, also skips
		                               steps that had errors in the original run (e.g., modal close buttons that
		                               auto-dismissed, or elements that became non-interactable)
		                delay_between_actions: Delay between actions in seconds (used when no saved interval)
		                max_step_interval: Maximum delay from saved step_interval (caps LLM time from original run)
		                summary_llm: Optional LLM to use for generating the final summary. If not provided, uses the agent's LLM
		                ai_step_llm: Optional LLM to use for AI steps (extract actions). If not provided, uses the agent's LLM
		                wait_for_elements: If True, wait for minimum number of elements before attempting element
		                               matching. Useful for SPA pages where shadow DOM content loads dynamically.
		                               Default is False.

		Returns:
		                List of action results (including AI summary as the final result)
		"""
		# Skip cloud sync session events for rerunning (we're replaying, not starting new)
		self.state.session_initialized = True

		# Initialize browser session
		await self.browser_session.start()

		results = []

		# Track previous step for redundant retry detection
		previous_item: AgentHistory | None = None
		previous_step_succeeded: bool = False

		try:
			for i, history_item in enumerate(history.history):
				goal = history_item.model_output.current_state.next_goal if history_item.model_output else ''
				step_num = history_item.metadata.step_number if history_item.metadata else i
				step_name = 'Initial actions' if step_num == 0 else f'Step {step_num}'

				# Determine step delay
				if history_item.metadata and history_item.metadata.step_interval is not None:
					# Cap the saved interval to max_step_interval (saved interval includes LLM time)
					step_delay = min(history_item.metadata.step_interval, max_step_interval)
					# Format delay nicely - show ms for values < 1s, otherwise show seconds
					if step_delay < 1.0:
						delay_str = f'{step_delay * 1000:.0f}ms'
					else:
						delay_str = f'{step_delay:.1f}s'
					if history_item.metadata.step_interval > max_step_interval:
						delay_source = f'capped to {delay_str} (saved was {history_item.metadata.step_interval:.1f}s)'
					else:
						delay_source = f'using saved step_interval={delay_str}'
				else:
					step_delay = delay_between_actions
					if step_delay < 1.0:
						delay_str = f'{step_delay * 1000:.0f}ms'
					else:
						delay_str = f'{step_delay:.1f}s'
					delay_source = f'using default delay={delay_str}'

				self.logger.info(f'Replaying {step_name} ({i + 1}/{len(history.history)}) [{delay_source}]: {goal}')

				if (
					not history_item.model_output
					or not history_item.model_output.action
					or history_item.model_output.action == [None]
				):
					self.logger.warning(f'{step_name}: No action to replay, skipping')
					results.append(ActionResult(error='No action to replay'))
					continue

				# Check if the original step had errors - skip if skip_failures is enabled
				original_had_error = any(r.error for r in history_item.result if r.error)
				if original_had_error and skip_failures:
					error_msgs = [r.error for r in history_item.result if r.error]
					self.logger.warning(
						f'{step_name}: Original step had error(s), skipping (skip_failures=True): {error_msgs[0][:100] if error_msgs else "unknown"}'
					)
					results.append(
						ActionResult(
							error=f'Skipped - original step had error: {error_msgs[0][:100] if error_msgs else "unknown"}'
						)
					)
					continue

				# Check if this step is a redundant retry of the previous step
				# This handles cases where original run needed to click same element multiple times
				# due to slow page response, but during replay the first click already worked
				if self._is_redundant_retry_step(history_item, previous_item, previous_step_succeeded):
					self.logger.info(f'{step_name}: Skipping redundant retry (previous step already succeeded with same element)')
					results.append(
						ActionResult(
							extracted_content='Skipped - redundant retry of previous step',
							include_in_memory=False,
						)
					)
					# Don't update previous_item/previous_step_succeeded - keep tracking the original step
					continue

				retry_count = 0
				step_succeeded = False
				menu_reopened = False  # Track if we've already tried reopening the menu
				# Exponential backoff: 5s base, doubling each retry, capped at 30s
				base_retry_delay = 5.0
				max_retry_delay = 30.0
				while retry_count < max_retries:
					try:
						result = await self._execute_history_step(history_item, step_delay, ai_step_llm, wait_for_elements)
						results.extend(result)
						step_succeeded = True
						break

					except Exception as e:
						error_str = str(e)
						retry_count += 1

						# Check if this is a "Could not find matching element" error for a menu item
						# If so, try to re-open the dropdown from the previous step before retrying
						if (
							not menu_reopened
							and 'Could not find matching element' in error_str
							and previous_item is not None
							and self._is_menu_opener_step(previous_item)
						):
							# Check if current step targets a menu item element
							curr_elements = history_item.state.interacted_element if history_item.state else []
							curr_elem = curr_elements[0] if curr_elements else None
							if self._is_menu_item_element(curr_elem):
								self.logger.info(
									'🔄 Dropdown may have closed. Attempting to re-open by re-executing previous step...'
								)
								reopened = await self._reexecute_menu_opener(previous_item, ai_step_llm)
								if reopened:
									menu_reopened = True
									# Don't increment retry_count for the menu reopen attempt
									# Retry immediately with minimal delay
									retry_count -= 1
									step_delay = 0.5  # Use short delay after reopening
									self.logger.info('🔄 Dropdown re-opened, retrying element match...')
									continue

						if retry_count == max_retries:
							error_msg = f'{step_name} failed after {max_retries} attempts: {error_str}'
							self.logger.error(error_msg)
							# Always record the error in results so AI summary counts it correctly
							results.append(ActionResult(error=error_msg))
							if not skip_failures:
								raise RuntimeError(error_msg)
							# With skip_failures=True, continue to next step
						else:
							# Exponential backoff: 5s, 10s, 20s, ... capped at 30s
							retry_delay = min(base_retry_delay * (2 ** (retry_count - 1)), max_retry_delay)
							self.logger.warning(
								f'{step_name} failed (attempt {retry_count}/{max_retries}), retrying in {retry_delay}s...'
							)
							await asyncio.sleep(retry_delay)

				# Update tracking for redundant retry detection
				previous_item = history_item
				previous_step_succeeded = step_succeeded

			# Generate AI summary of rerun completion
			self.logger.info('🤖 Generating AI summary of rerun completion...')
			summary_result = await self._generate_rerun_summary(self.task, results, summary_llm)
			results.append(summary_result)

			return results
		finally:
			# Always close resources, even on failure
			await self.close()