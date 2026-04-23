async def test_custom_dropdown(self, tools, browser_session: BrowserSession, base_url):
		"""Test get_dropdown_options with custom dropdown implementation."""
		# Navigate to the custom dropdown test page
		await tools.navigate(url=f'{base_url}/custom-dropdown', new_tab=False, browser_session=browser_session)

		# Initialize the DOM state
		await browser_session.get_browser_state_summary()

		# Find the custom dropdown by ID
		dropdown_index = await browser_session.get_index_by_id('custom-dropdown')

		assert dropdown_index is not None, 'Could not find custom dropdown element'

		# Test via tools action
		result = await tools.dropdown_options(index=dropdown_index, browser_session=browser_session)

		# Verify the result
		assert isinstance(result, ActionResult)
		assert result.extracted_content is not None

		# Verify expected custom dropdown options are present
		expected_options = ['Red', 'Green', 'Blue', 'Yellow']
		for option in expected_options:
			assert option in result.extracted_content, f"Option '{option}' not found in result content"

		# Also test direct event dispatch
		node = await browser_session.get_element_by_index(dropdown_index)
		assert node is not None
		event = browser_session.event_bus.dispatch(GetDropdownOptionsEvent(node=node))
		dropdown_data = await event.event_result(timeout=3.0)

		assert dropdown_data is not None
		assert 'options' in dropdown_data
		assert 'type' in dropdown_data
		assert dropdown_data['type'] == 'custom'