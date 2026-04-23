async def get_browser_state_summary(
		self,
		include_screenshot: bool = True,
		cached: bool = False,
		include_recent_events: bool = False,
	) -> BrowserStateSummary:
		if cached and self._cached_browser_state_summary is not None and self._cached_browser_state_summary.dom_state:
			# Don't use cached state if it has 0 interactive elements
			selector_map = self._cached_browser_state_summary.dom_state.selector_map

			# Don't use cached state if we need a screenshot but the cached state doesn't have one
			if include_screenshot and not self._cached_browser_state_summary.screenshot:
				self.logger.debug('⚠️ Cached browser state has no screenshot, fetching fresh state with screenshot')
				# Fall through to fetch fresh state with screenshot
			elif selector_map and len(selector_map) > 0:
				self.logger.debug('🔄 Using pre-cached browser state summary for open tab')
				return self._cached_browser_state_summary
			else:
				self.logger.debug('⚠️ Cached browser state has 0 interactive elements, fetching fresh state')
				# Fall through to fetch fresh state

		# Dispatch the event and wait for result
		event: BrowserStateRequestEvent = cast(
			BrowserStateRequestEvent,
			self.event_bus.dispatch(
				BrowserStateRequestEvent(
					include_dom=True,
					include_screenshot=include_screenshot,
					include_recent_events=include_recent_events,
				)
			),
		)

		# The handler returns the BrowserStateSummary directly
		result = await event.event_result(raise_if_none=True, raise_if_any=True)
		assert result is not None and result.dom_state is not None
		return result