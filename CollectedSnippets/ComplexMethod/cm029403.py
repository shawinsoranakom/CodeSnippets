async def _click_by_index(
			params: ClickElementAction | ClickElementActionIndexOnly, browser_session: BrowserSession
		) -> ActionResult:
			assert params.index is not None
			try:
				assert params.index != 0, (
					'Cannot click on element with index 0. If there are no interactive elements use wait(), refresh(), etc. to troubleshoot'
				)

				# Look up the node from the selector map
				node = await browser_session.get_element_by_index(params.index)
				if node is None:
					msg = f'Element index {params.index} not available - page may have changed. Try refreshing browser state.'
					logger.warning(f'⚠️ {msg}')
					return ActionResult(extracted_content=msg)

				# Get description of clicked element
				element_desc = get_click_description(node)

				# Capture tab IDs before click to detect new tabs
				tabs_before = {t.target_id for t in await browser_session.get_tabs()}

				# Highlight the element being clicked (truly non-blocking)
				create_task_with_error_handling(
					browser_session.highlight_interaction_element(node), name='highlight_click_element', suppress_exceptions=True
				)

				event = browser_session.event_bus.dispatch(ClickElementEvent(node=node))
				await event
				# Wait for handler to complete and get any exception or metadata
				click_metadata = await event.event_result(raise_if_any=True, raise_if_none=False)

				# Check if result contains validation error (e.g., trying to click <select> or file input)
				if isinstance(click_metadata, dict) and 'validation_error' in click_metadata:
					error_msg = click_metadata['validation_error']
					# If it's a select element, try to get dropdown options as a helpful shortcut
					if 'Cannot click on <select> elements.' in error_msg:
						try:
							return await dropdown_options(
								params=GetDropdownOptionsAction(index=params.index), browser_session=browser_session
							)
						except Exception as dropdown_error:
							logger.debug(
								f'Failed to get dropdown options as shortcut during click on dropdown: {type(dropdown_error).__name__}: {dropdown_error}'
							)
					return ActionResult(error=error_msg)

				# Build memory with element info
				memory = f'Clicked {element_desc}'
				memory += await _detect_new_tab_opened(browser_session, tabs_before)
				logger.info(f'🖱️ {memory}')

				# Include click coordinates in metadata if available
				return ActionResult(
					extracted_content=memory,
					metadata=click_metadata if isinstance(click_metadata, dict) else None,
				)
			except BrowserError as e:
				return handle_browser_error(e)
			except Exception as e:
				error_msg = f'Failed to click element {params.index}: {str(e)}'
				return ActionResult(error=error_msg)