async def test_native_select_dropdown(self, tools, browser_session: BrowserSession, base_url):
		"""Test get_dropdown_options with native HTML select element."""
		# Navigate to the native dropdown test page
		await tools.navigate(url=f'{base_url}/native-dropdown', new_tab=False, browser_session=browser_session)

		# Initialize the DOM state to populate the selector map
		await browser_session.get_browser_state_summary()

		# Find the select element by ID
		dropdown_index = await browser_session.get_index_by_id('test-dropdown')

		assert dropdown_index is not None, 'Could not find select element'

		# Test via tools action
		result = await tools.dropdown_options(index=dropdown_index, browser_session=browser_session)

		# Verify the result
		assert isinstance(result, ActionResult)
		assert result.extracted_content is not None

		# Verify all expected options are present
		expected_options = ['Please select', 'First Option', 'Second Option', 'Third Option']
		for option in expected_options:
			assert option in result.extracted_content, f"Option '{option}' not found in result content"

		# Verify instruction is included
		assert 'Use the exact text string' in result.extracted_content and 'select_dropdown' in result.extracted_content

		# Also test direct event dispatch
		node = await browser_session.get_element_by_index(dropdown_index)
		assert node is not None
		event = browser_session.event_bus.dispatch(GetDropdownOptionsEvent(node=node))
		dropdown_data = await event.event_result(timeout=3.0)

		assert dropdown_data is not None
		assert 'options' in dropdown_data
		assert 'type' in dropdown_data
		assert dropdown_data['type'] == 'select'