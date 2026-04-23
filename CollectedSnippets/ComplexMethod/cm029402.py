async def _click_by_coordinate(params: ClickElementAction, browser_session: BrowserSession) -> ActionResult:
			# Ensure coordinates are provided (type safety)
			if params.coordinate_x is None or params.coordinate_y is None:
				return ActionResult(error='Both coordinate_x and coordinate_y must be provided')

			try:
				# Convert coordinates from LLM size to original viewport size if resizing was used
				actual_x, actual_y = _convert_llm_coordinates_to_viewport(
					params.coordinate_x, params.coordinate_y, browser_session
				)

				# Capture tab IDs before click to detect new tabs
				tabs_before = {t.target_id for t in await browser_session.get_tabs()}

				# Highlight the coordinate being clicked (truly non-blocking)
				asyncio.create_task(browser_session.highlight_coordinate_click(actual_x, actual_y))

				# Dispatch ClickCoordinateEvent - handler will check for safety and click
				event = browser_session.event_bus.dispatch(
					ClickCoordinateEvent(coordinate_x=actual_x, coordinate_y=actual_y, force=True)
				)
				await event
				# Wait for handler to complete and get any exception or metadata
				click_metadata = await event.event_result(raise_if_any=True, raise_if_none=False)

				# Check for validation errors (only happens when force=False)
				if isinstance(click_metadata, dict) and 'validation_error' in click_metadata:
					error_msg = click_metadata['validation_error']
					return ActionResult(error=error_msg)

				memory = f'Clicked on coordinate {params.coordinate_x}, {params.coordinate_y}'
				memory += await _detect_new_tab_opened(browser_session, tabs_before)
				logger.info(f'🖱️ {memory}')

				return ActionResult(
					extracted_content=memory,
					metadata={'click_x': actual_x, 'click_y': actual_y},
				)
			except BrowserError as e:
				return handle_browser_error(e)
			except Exception as e:
				error_msg = f'Failed to click at coordinates ({params.coordinate_x}, {params.coordinate_y}).'
				return ActionResult(error=error_msg)