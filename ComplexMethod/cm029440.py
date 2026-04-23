async def _get_browser_state(self, include_screenshot: bool = False) -> tuple[str, str | None]:
		"""Get current browser state. Returns (state_json, screenshot_b64 | None)."""
		if not self.browser_session:
			return 'Error: No browser session active', None

		state = await self.browser_session.get_browser_state_summary()

		result: dict[str, Any] = {
			'url': state.url,
			'title': state.title,
			'tabs': [{'url': tab.url, 'title': tab.title} for tab in state.tabs],
			'interactive_elements': [],
		}

		# Add viewport info so the LLM knows the coordinate space
		if state.page_info:
			pi = state.page_info
			result['viewport'] = {
				'width': pi.viewport_width,
				'height': pi.viewport_height,
			}
			result['page'] = {
				'width': pi.page_width,
				'height': pi.page_height,
			}
			result['scroll'] = {
				'x': pi.scroll_x,
				'y': pi.scroll_y,
			}

		# Add interactive elements with their indices
		for index, element in state.dom_state.selector_map.items():
			elem_info: dict[str, Any] = {
				'index': index,
				'tag': element.tag_name,
				'text': element.get_all_children_text(max_depth=2)[:100],
			}
			if element.attributes.get('placeholder'):
				elem_info['placeholder'] = element.attributes['placeholder']
			if element.attributes.get('href'):
				elem_info['href'] = element.attributes['href']
			result['interactive_elements'].append(elem_info)

		# Return screenshot separately as ImageContent instead of embedding base64 in JSON
		screenshot_b64 = None
		if include_screenshot and state.screenshot:
			screenshot_b64 = state.screenshot
			# Include viewport dimensions in JSON so LLM can map pixels to coordinates
			if state.page_info:
				result['screenshot_dimensions'] = {
					'width': state.page_info.viewport_width,
					'height': state.page_info.viewport_height,
				}

		return json.dumps(result, indent=2), screenshot_b64