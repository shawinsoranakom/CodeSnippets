async def test_aria_menu_dropdown(self, tools, browser_session: BrowserSession, base_url):
		"""Test get_dropdown_options with ARIA role='menu' element."""
		# Navigate to the ARIA menu test page
		await tools.navigate(url=f'{base_url}/aria-menu', new_tab=False, browser_session=browser_session)

		# Initialize the DOM state
		await browser_session.get_browser_state_summary()

		# Find the ARIA menu by ID
		menu_index = await browser_session.get_index_by_id('pyNavigation1752753375773')

		assert menu_index is not None, 'Could not find ARIA menu element'

		# Test via tools action
		result = await tools.dropdown_options(index=menu_index, browser_session=browser_session)

		# Verify the result
		assert isinstance(result, ActionResult)
		assert result.extracted_content is not None

		# Verify expected ARIA menu options are present
		expected_options = ['Filter', 'Sort', 'Appearance', 'Summarize', 'Delete']
		for option in expected_options:
			assert option in result.extracted_content, f"Option '{option}' not found in result content"

		# Also test direct event dispatch
		node = await browser_session.get_element_by_index(menu_index)
		assert node is not None
		event = browser_session.event_bus.dispatch(GetDropdownOptionsEvent(node=node))
		dropdown_data = await event.event_result(timeout=3.0)

		assert dropdown_data is not None
		assert 'options' in dropdown_data
		assert 'type' in dropdown_data
		assert dropdown_data['type'] == 'aria'