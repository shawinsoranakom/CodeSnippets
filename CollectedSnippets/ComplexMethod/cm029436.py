async def _execute_tool(
		self, tool_name: str, arguments: dict[str, Any]
	) -> str | list[types.TextContent | types.ImageContent]:
		"""Execute a browser-use tool. Returns str for most tools, or a content list for tools with image output."""

		# Agent-based tools
		if tool_name == 'retry_with_browser_use_agent':
			return await self._retry_with_browser_use_agent(
				task=arguments['task'],
				max_steps=arguments.get('max_steps', 100),
				model=arguments.get('model'),
				allowed_domains=arguments.get('allowed_domains', []),
				use_vision=arguments.get('use_vision', True),
			)

		# Browser session management tools (don't require active session)
		if tool_name == 'browser_list_sessions':
			return await self._list_sessions()

		elif tool_name == 'browser_close_session':
			return await self._close_session(arguments['session_id'])

		elif tool_name == 'browser_close_all':
			return await self._close_all_sessions()

		# Direct browser control tools (require active session)
		elif tool_name.startswith('browser_'):
			# Ensure browser session exists
			if not self.browser_session:
				await self._init_browser_session()

			if tool_name == 'browser_navigate':
				return await self._navigate(arguments['url'], arguments.get('new_tab', False))

			elif tool_name == 'browser_click':
				return await self._click(
					index=arguments.get('index'),
					coordinate_x=arguments.get('coordinate_x'),
					coordinate_y=arguments.get('coordinate_y'),
					new_tab=arguments.get('new_tab', False),
				)

			elif tool_name == 'browser_type':
				return await self._type_text(arguments['index'], arguments['text'])

			elif tool_name == 'browser_get_state':
				state_json, screenshot_b64 = await self._get_browser_state(arguments.get('include_screenshot', False))
				content: list[types.TextContent | types.ImageContent] = [types.TextContent(type='text', text=state_json)]
				if screenshot_b64:
					content.append(types.ImageContent(type='image', data=screenshot_b64, mimeType='image/png'))
				return content

			elif tool_name == 'browser_get_html':
				return await self._get_html(arguments.get('selector'))

			elif tool_name == 'browser_screenshot':
				meta_json, screenshot_b64 = await self._screenshot(arguments.get('full_page', False))
				content: list[types.TextContent | types.ImageContent] = [types.TextContent(type='text', text=meta_json)]
				if screenshot_b64:
					content.append(types.ImageContent(type='image', data=screenshot_b64, mimeType='image/png'))
				return content

			elif tool_name == 'browser_extract_content':
				return await self._extract_content(arguments['query'], arguments.get('extract_links', False))

			elif tool_name == 'browser_scroll':
				return await self._scroll(arguments.get('direction', 'down'))

			elif tool_name == 'browser_go_back':
				return await self._go_back()

			elif tool_name == 'browser_close':
				return await self._close_browser()

			elif tool_name == 'browser_list_tabs':
				return await self._list_tabs()

			elif tool_name == 'browser_switch_tab':
				return await self._switch_tab(arguments['tab_id'])

			elif tool_name == 'browser_close_tab':
				return await self._close_tab(arguments['tab_id'])

		return f'Unknown tool: {tool_name}'