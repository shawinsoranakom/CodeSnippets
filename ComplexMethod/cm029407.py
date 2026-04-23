async def scroll(params: ScrollAction, browser_session: BrowserSession):
			try:
				# Look up the node from the selector map if index is provided
				# Special case: index 0 means scroll the whole page (root/body element)
				node = None
				if params.index is not None and params.index != 0:
					node = await browser_session.get_element_by_index(params.index)
					if node is None:
						# Element does not exist
						msg = f'Element index {params.index} not found in browser state'
						return ActionResult(error=msg)

				direction = 'down' if params.down else 'up'
				target = f'element {params.index}' if params.index is not None and params.index != 0 else ''

				# Get actual viewport height for more accurate scrolling
				try:
					cdp_session = await browser_session.get_or_create_cdp_session()
					metrics = await cdp_session.cdp_client.send.Page.getLayoutMetrics(session_id=cdp_session.session_id)

					# Use cssVisualViewport for the most accurate representation
					css_viewport = metrics.get('cssVisualViewport', {})
					css_layout_viewport = metrics.get('cssLayoutViewport', {})

					# Get viewport height, prioritizing cssVisualViewport
					viewport_height = int(css_viewport.get('clientHeight') or css_layout_viewport.get('clientHeight', 1000))

					logger.debug(f'Detected viewport height: {viewport_height}px')
				except Exception as e:
					viewport_height = 1000  # Fallback to 1000px
					logger.debug(f'Failed to get viewport height, using fallback 1000px: {e}')

				# For multiple pages (>=1.0), scroll one page at a time to ensure each scroll completes
				if params.pages >= 1.0:
					import asyncio

					num_full_pages = int(params.pages)
					remaining_fraction = params.pages - num_full_pages

					completed_scrolls = 0

					# Scroll one page at a time
					for i in range(num_full_pages):
						try:
							pixels = viewport_height  # Use actual viewport height
							if not params.down:
								pixels = -pixels

							event = browser_session.event_bus.dispatch(
								ScrollEvent(direction=direction, amount=abs(pixels), node=node)
							)
							await event
							await event.event_result(raise_if_any=True, raise_if_none=False)
							completed_scrolls += 1

							# Small delay to ensure scroll completes before next one
							await asyncio.sleep(0.15)

						except Exception as e:
							logger.warning(f'Scroll {i + 1}/{num_full_pages} failed: {e}')
							# Continue with remaining scrolls even if one fails

					# Handle fractional page if present
					if remaining_fraction > 0:
						try:
							pixels = int(remaining_fraction * viewport_height)
							if not params.down:
								pixels = -pixels

							event = browser_session.event_bus.dispatch(
								ScrollEvent(direction=direction, amount=abs(pixels), node=node)
							)
							await event
							await event.event_result(raise_if_any=True, raise_if_none=False)
							completed_scrolls += remaining_fraction

						except Exception as e:
							logger.warning(f'Fractional scroll failed: {e}')

					if params.pages == 1.0:
						long_term_memory = f'Scrolled {direction} {target} {viewport_height}px'.replace('  ', ' ')
					else:
						long_term_memory = f'Scrolled {direction} {target} {completed_scrolls:.1f} pages'.replace('  ', ' ')
				else:
					# For fractional pages <1.0, do single scroll
					pixels = int(params.pages * viewport_height)
					event = browser_session.event_bus.dispatch(
						ScrollEvent(direction='down' if params.down else 'up', amount=pixels, node=node)
					)
					await event
					await event.event_result(raise_if_any=True, raise_if_none=False)
					long_term_memory = f'Scrolled {direction} {target} {params.pages} pages'.replace('  ', ' ')

				msg = f'🔍 {long_term_memory}'
				logger.info(msg)
				return ActionResult(extracted_content=msg, long_term_memory=long_term_memory)
			except Exception as e:
				logger.error(f'Failed to dispatch ScrollEvent: {type(e).__name__}: {e}')
				error_msg = 'Failed to execute scroll action.'
				return ActionResult(error=error_msg)