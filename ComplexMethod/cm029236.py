async def _execute_history_step(
		self,
		history_item: AgentHistory,
		delay: float,
		ai_step_llm: BaseChatModel | None = None,
		wait_for_elements: bool = False,
	) -> list[ActionResult]:
		"""Execute a single step from history with element validation.

		For extract actions, uses AI to re-evaluate the content since page content may have changed.

		Args:
			history_item: The history step to execute
			delay: Delay before executing the step
			ai_step_llm: Optional LLM to use for AI steps
			wait_for_elements: If True, wait for minimum elements before element matching
		"""
		assert self.browser_session is not None, 'BrowserSession is not set up'

		await asyncio.sleep(delay)

		# Optionally wait for minimum elements before element matching (useful for SPAs)
		if wait_for_elements:
			# Determine if we need to wait for elements (actions that interact with DOM elements)
			needs_element_matching = False
			if history_item.model_output:
				for i, action in enumerate(history_item.model_output.action):
					action_data = action.model_dump(exclude_unset=True)
					action_name = next(iter(action_data.keys()), None)
					# Actions that need element matching
					if action_name in ('click', 'input', 'hover', 'select_option', 'drag_and_drop'):
						historical_elem = (
							history_item.state.interacted_element[i] if i < len(history_item.state.interacted_element) else None
						)
						if historical_elem is not None:
							needs_element_matching = True
							break

			# If we need element matching, wait for minimum elements before proceeding
			if needs_element_matching:
				min_elements = self._count_expected_elements_from_history(history_item)
				if min_elements > 0:
					state = await self._wait_for_minimum_elements(min_elements, timeout=15.0, poll_interval=1.0)
				else:
					state = await self.browser_session.get_browser_state_summary(include_screenshot=False)
			else:
				state = await self.browser_session.get_browser_state_summary(include_screenshot=False)
		else:
			state = await self.browser_session.get_browser_state_summary(include_screenshot=False)
		if not state or not history_item.model_output:
			raise ValueError('Invalid state or model output')

		results = []
		pending_actions = []

		for i, action in enumerate(history_item.model_output.action):
			# Check if this is an extract action - use AI step instead
			action_data = action.model_dump(exclude_unset=True)
			action_name = next(iter(action_data.keys()), None)

			if action_name == 'extract':
				# Execute any pending actions first to maintain correct order
				# (e.g., if step is [click, extract], click must happen before extract)
				if pending_actions:
					batch_results = await self.multi_act(pending_actions)
					results.extend(batch_results)
					pending_actions = []

				# Now execute AI step for extract action
				extract_params = action_data['extract']
				query = extract_params.get('query', '')
				extract_links = extract_params.get('extract_links', False)

				self.logger.info(f'🤖 Using AI step for extract action: {query[:50]}...')
				ai_result = await self._execute_ai_step(
					query=query,
					include_screenshot=False,  # Match original extract behavior
					extract_links=extract_links,
					ai_step_llm=ai_step_llm,
				)
				results.append(ai_result)
			else:
				# For non-extract actions, update indices and collect for batch execution
				historical_elem = history_item.state.interacted_element[i]
				updated_action = await self._update_action_indices(
					historical_elem,
					action,
					state,
				)
				if updated_action is None:
					# Build informative error message with diagnostic info
					elem_info = self._format_element_for_error(historical_elem)
					selector_map = state.dom_state.selector_map or {}
					selector_count = len(selector_map)

					# Find elements with same node_name for diagnostics
					hist_node = historical_elem.node_name.lower() if historical_elem else ''
					similar_elements = []
					if historical_elem and historical_elem.attributes:
						for idx, elem in selector_map.items():
							if elem.node_name.lower() == hist_node and elem.attributes:
								elem_aria = elem.attributes.get('aria-label', '')
								if elem_aria:
									similar_elements.append(f'{idx}:{elem_aria[:30]}')
									if len(similar_elements) >= 5:
										break

					diagnostic = ''
					if similar_elements:
						diagnostic = f'\n  Available <{hist_node.upper()}> with aria-label: {similar_elements}'
					elif hist_node:
						same_node_count = sum(1 for e in selector_map.values() if e.node_name.lower() == hist_node)
						diagnostic = (
							f'\n  Found {same_node_count} <{hist_node.upper()}> elements (none with matching identifiers)'
						)

					raise ValueError(
						f'Could not find matching element for action {i} in current page.\n'
						f'  Looking for: {elem_info}\n'
						f'  Page has {selector_count} interactive elements.{diagnostic}\n'
						f'  Tried: EXACT hash → STABLE hash → XPATH → AX_NAME → ATTRIBUTE matching'
					)
				pending_actions.append(updated_action)

		# Execute any remaining pending actions
		if pending_actions:
			batch_results = await self.multi_act(pending_actions)
			results.extend(batch_results)

		return results