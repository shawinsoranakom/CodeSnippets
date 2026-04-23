async def _click(
		self,
		index: int | None = None,
		coordinate_x: int | None = None,
		coordinate_y: int | None = None,
		new_tab: bool = False,
	) -> str:
		"""Click an element by index or at viewport coordinates."""
		if not self.browser_session:
			return 'Error: No browser session active'

		# Update session activity
		self._update_session_activity(self.browser_session.id)

		# Coordinate-based clicking
		if coordinate_x is not None and coordinate_y is not None:
			from browser_use.browser.events import ClickCoordinateEvent

			event = self.browser_session.event_bus.dispatch(
				ClickCoordinateEvent(coordinate_x=coordinate_x, coordinate_y=coordinate_y)
			)
			await event
			return f'Clicked at coordinates ({coordinate_x}, {coordinate_y})'

		# Index-based clicking
		if index is None:
			return 'Error: Provide either index or both coordinate_x and coordinate_y'

		# Get the element
		element = await self.browser_session.get_dom_element_by_index(index)
		if not element:
			return f'Element with index {index} not found'

		if new_tab:
			# For links, extract href and open in new tab
			href = element.attributes.get('href')
			if href:
				# Convert relative href to absolute URL
				state = await self.browser_session.get_browser_state_summary()
				current_url = state.url
				if href.startswith('/'):
					# Relative URL - construct full URL
					from urllib.parse import urlparse

					parsed = urlparse(current_url)
					full_url = f'{parsed.scheme}://{parsed.netloc}{href}'
				else:
					full_url = href

				# Open link in new tab
				from browser_use.browser.events import NavigateToUrlEvent

				event = self.browser_session.event_bus.dispatch(NavigateToUrlEvent(url=full_url, new_tab=True))
				await event
				return f'Clicked element {index} and opened in new tab {full_url[:20]}...'
			else:
				# For non-link elements, just do a normal click
				from browser_use.browser.events import ClickElementEvent

				event = self.browser_session.event_bus.dispatch(ClickElementEvent(node=element))
				await event
				return f'Clicked element {index} (new tab not supported for non-link elements)'
		else:
			# Normal click
			from browser_use.browser.events import ClickElementEvent

			event = self.browser_session.event_bus.dispatch(ClickElementEvent(node=element))
			await event
			return f'Clicked element {index}'