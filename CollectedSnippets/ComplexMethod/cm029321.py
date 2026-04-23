async def on_ScrollEvent(self, event: ScrollEvent) -> None:
		"""Handle scroll request with CDP."""
		# Check if we have a current target for scrolling
		if not self.browser_session.agent_focus_target_id:
			error_msg = 'No active target for scrolling'
			raise BrowserError(error_msg)

		try:

			def invalidate_dom_cache() -> None:
				if self.browser_session._dom_watchdog:
					self.browser_session._dom_watchdog.clear_cache()

			# Convert direction and amount to pixels
			# Positive pixels = scroll down, negative = scroll up
			pixels = event.amount if event.direction == 'down' else -event.amount

			# Element-specific scrolling if node is provided
			if event.node is not None:
				element_node = event.node
				index_for_logging = element_node.backend_node_id or 'unknown'

				# Check if the element is an iframe
				is_iframe = element_node.tag_name and element_node.tag_name.upper() == 'IFRAME'

				# Try to scroll the element's container
				success = await self._scroll_element_container(element_node, pixels)
				if success:
					self.logger.debug(
						f'📜 Scrolled element {index_for_logging} container {event.direction} by {event.amount} pixels'
					)

					# For iframe scrolling, we need to force a full DOM refresh
					# because the iframe's content has changed position
					if is_iframe:
						self.logger.debug('🔄 Forcing DOM refresh after iframe scroll')
						# Note: We don't clear cached state here - let multi_act handle DOM change detection
						# by explicitly rebuilding and comparing when needed

						# Wait a bit for the scroll to settle and DOM to update
						await asyncio.sleep(0.2)

					invalidate_dom_cache()
					return None

			# Perform target-level scroll
			await self._scroll_with_cdp_gesture(pixels)

			# Note: We don't clear cached state here - let multi_act handle DOM change detection
			# by explicitly rebuilding and comparing when needed
			invalidate_dom_cache()

			# Log success
			self.logger.debug(f'📜 Scrolled {event.direction} by {event.amount} pixels')
			return None
		except Exception as e:
			raise