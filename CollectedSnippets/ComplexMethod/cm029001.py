async def test_get_dropdown_options_with_nested_aria_menu(self, tools, browser_session: BrowserSession, base_url):
		"""Test that get_dropdown_options can handle nested ARIA menus (like Sort submenu)."""
		# Navigate to the ARIA menu test page
		await tools.navigate(url=f'{base_url}/aria-menu', new_tab=False, browser_session=browser_session)

		# Wait for the page to load
		from browser_use.browser.events import NavigationCompleteEvent

		await browser_session.event_bus.expect(NavigationCompleteEvent, timeout=10.0)

		# Initialize the DOM state to populate the selector map
		await browser_session.get_browser_state_summary()

		# Get the selector map
		selector_map = await browser_session.get_selector_map()

		# Find the nested ARIA menu element in the selector map
		nested_menu_index = None
		for idx, element in selector_map.items():
			# Look for the nested UL with id containing "$PpyNavigation"
			if (
				element.tag_name.lower() == 'ul'
				and '$PpyNavigation' in str(element.attributes.get('id', ''))
				and element.attributes.get('role') == 'menu'
			):
				nested_menu_index = idx
				break

		# The nested menu might not be in the selector map initially if it's hidden
		# In that case, we should test the main menu
		if nested_menu_index is None:
			# Find the main menu instead
			for idx, element in selector_map.items():
				if element.tag_name.lower() == 'ul' and element.attributes.get('id') == 'pyNavigation1752753375773':
					nested_menu_index = idx
					break

		assert nested_menu_index is not None, (
			f'Could not find any ARIA menu element in selector map. Available elements: {[f"{idx}: {element.tag_name}" for idx, element in selector_map.items()]}'
		)

		# Execute the action with the menu index
		result = await tools.dropdown_options(index=nested_menu_index, browser_session=browser_session)

		# Verify the result structure
		assert isinstance(result, ActionResult)
		assert result.extracted_content is not None

		# The action should return some menu options
		assert 'Use the exact text string in select_dropdown' in result.extracted_content