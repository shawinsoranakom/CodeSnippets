async def test_get_dropdown_options(self, tools, browser_session, base_url, http_server):
		"""Test that get_dropdown_options correctly retrieves options from a dropdown."""
		# Add route for dropdown test page
		http_server.expect_request('/dropdown1').respond_with_data(
			"""
			<!DOCTYPE html>
			<html>
			<head>
				<title>Dropdown Test</title>
			</head>
			<body>
				<h1>Dropdown Test</h1>
				<select id="test-dropdown" name="test-dropdown">
					<option value="">Please select</option>
					<option value="option1">First Option</option>
					<option value="option2">Second Option</option>
					<option value="option3">Third Option</option>
				</select>
			</body>
			</html>
			""",
			content_type='text/html',
		)

		# Navigate to the dropdown test page
		await tools.navigate(url=f'{base_url}/dropdown1', new_tab=False, browser_session=browser_session)

		# Wait for the page to load using CDP
		cdp_session = await browser_session.get_or_create_cdp_session()
		assert cdp_session is not None, 'CDP session not initialized'

		# Wait for page load by checking document ready state
		await asyncio.sleep(0.5)  # Brief wait for navigation to start
		ready_state = await cdp_session.cdp_client.send.Runtime.evaluate(
			params={'expression': 'document.readyState'}, session_id=cdp_session.session_id
		)
		# If not complete, wait a bit more
		if ready_state.get('result', {}).get('value') != 'complete':
			await asyncio.sleep(1.0)

		# Initialize the DOM state to populate the selector map
		await browser_session.get_browser_state_summary()

		# Get the selector map
		selector_map = await browser_session.get_selector_map()

		# Find the dropdown element in the selector map
		dropdown_index = None
		for idx, element in selector_map.items():
			if element.tag_name.lower() == 'select':
				dropdown_index = idx
				break

		assert dropdown_index is not None, (
			f'Could not find select element in selector map. Available elements: {[f"{idx}: {element.tag_name}" for idx, element in selector_map.items()]}'
		)

		# Execute the action with the dropdown index
		result = await tools.dropdown_options(index=dropdown_index, browser_session=browser_session)

		expected_options = [
			{'index': 0, 'text': 'Please select', 'value': ''},
			{'index': 1, 'text': 'First Option', 'value': 'option1'},
			{'index': 2, 'text': 'Second Option', 'value': 'option2'},
			{'index': 3, 'text': 'Third Option', 'value': 'option3'},
		]

		# Verify the result structure
		assert isinstance(result, ActionResult)

		# Core logic validation: Verify all options are returned
		assert result.extracted_content is not None
		for option in expected_options[1:]:  # Skip the placeholder option
			assert option['text'] in result.extracted_content, f"Option '{option['text']}' not found in result content"

		# Verify the instruction for using the text in select_dropdown is included
		assert 'Use the exact text or value string' in result.extracted_content and 'select_dropdown' in result.extracted_content

		# Verify the actual dropdown options in the DOM using CDP
		dropdown_options_result = await cdp_session.cdp_client.send.Runtime.evaluate(
			params={
				'expression': """
					JSON.stringify((() => {
						const select = document.getElementById('test-dropdown');
						return Array.from(select.options).map(opt => ({
							text: opt.text,
							value: opt.value
						}));
					})())
				""",
				'returnByValue': True,
			},
			session_id=cdp_session.session_id,
		)
		dropdown_options_json = dropdown_options_result.get('result', {}).get('value', '[]')
		import json

		dropdown_options = json.loads(dropdown_options_json) if isinstance(dropdown_options_json, str) else dropdown_options_json

		# Verify the dropdown has the expected options
		assert len(dropdown_options) == len(expected_options), (
			f'Expected {len(expected_options)} options, got {len(dropdown_options)}'
		)
		for i, expected in enumerate(expected_options):
			actual = dropdown_options[i]
			assert actual['text'] == expected['text'], (
				f"Option at index {i} has wrong text: expected '{expected['text']}', got '{actual['text']}'"
			)
			assert actual['value'] == expected['value'], (
				f"Option at index {i} has wrong value: expected '{expected['value']}', got '{actual['value']}'"
			)