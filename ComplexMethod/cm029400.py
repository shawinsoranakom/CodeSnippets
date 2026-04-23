async def act(
		self,
		action: ActionModel,
		browser_session: BrowserSession,
		page_extraction_llm: BaseChatModel | None = None,
		sensitive_data: dict[str, str | dict[str, str]] | None = None,
		available_file_paths: list[str] | None = None,
		file_system: FileSystem | None = None,
		extraction_schema: dict | None = None,
		action_timeout: float | None = None,
	) -> ActionResult:
		"""Execute an action.

		action_timeout: per-action wall-clock cap (seconds). Prevents actions from hanging
		indefinitely when a CDP WebSocket goes silent — a common failure mode with remote
		browsers where internal CDP calls (tab switches, lifecycle waits) have no timeouts.
		Defaults to BROWSER_USE_ACTION_TIMEOUT_S env var or 180s (above the 120s
		page_extraction_llm cap used by the `extract` action).
		"""

		timeout_s = _coerce_valid_action_timeout(action_timeout)

		for action_name, params in action.model_dump(exclude_unset=True).items():
			if params is not None:
				# Use Laminar span if available, otherwise use no-op context manager
				if Laminar is not None:
					span_context = Laminar.start_as_current_span(
						name=action_name,
						input={
							'action': action_name,
							'params': params,
						},
						span_type='TOOL',
					)
				else:
					# No-op context manager when lmnr is not available
					from contextlib import nullcontext

					span_context = nullcontext()

				with span_context:
					try:
						result = await asyncio.wait_for(
							self.registry.execute_action(
								action_name=action_name,
								params=params,
								browser_session=browser_session,
								page_extraction_llm=page_extraction_llm,
								file_system=file_system,
								sensitive_data=sensitive_data,
								available_file_paths=available_file_paths,
								extraction_schema=extraction_schema,
							),
							timeout=timeout_s,
						)
					except BrowserError as e:
						logger.error(f'❌ Action {action_name} failed with BrowserError: {str(e)}')
						result = handle_browser_error(e)
					except TimeoutError:
						# Covers both the per-action asyncio.wait_for cap and any inner
						# TimeoutError that bubbled out of the handler.
						logger.error(
							f'❌ Action {action_name} hit the per-action timeout ({timeout_s:.0f}s) '
							f'— likely an unresponsive CDP connection. Returning error so the agent can recover.'
						)
						result = ActionResult(
							error=(
								f'Action {action_name} timed out after {timeout_s:.0f}s. '
								f'The browser may be unresponsive (dead CDP WebSocket). '
								f'Try again or a different approach.'
							)
						)
					except Exception as e:
						# Log the original exception with traceback for observability
						logger.error(f"Action '{action_name}' failed with error: {str(e)}")
						result = ActionResult(error=str(e))

					if Laminar is not None:
						Laminar.set_span_output(result)

				if isinstance(result, str):
					return ActionResult(extracted_content=result)
				elif isinstance(result, ActionResult):
					return result
				elif result is None:
					return ActionResult()
				else:
					raise ValueError(f'Invalid action result type: {type(result)} of {result}')
		return ActionResult()