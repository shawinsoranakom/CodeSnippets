async def test_select_dropdown_option(self, tools, browser_session, base_url, http_server):
		"""Test that select_dropdown_option correctly selects an option from a dropdown."""
		# Add route for dropdown test page
		http_server.expect_request('/dropdown2').respond_with_data(
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
		await tools.navigate(url=f'{base_url}/dropdown2', new_tab=False, browser_session=browser_session)

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

		# populate the selector map with highlight indices
		await browser_session.get_browser_state_summary()

		# Now get the selector map which should contain our dropdown
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
		result = await tools.select_dropdown(index=dropdown_index, text='Second Option', browser_session=browser_session)

		# Verify the result structure
		assert isinstance(result, ActionResult)

		# Core logic validation: Verify selection was successful
		assert result.extracted_content is not None
		assert 'selected option' in result.extracted_content.lower()
		assert 'Second Option' in result.extracted_content

		# Verify the actual dropdown selection was made by checking the DOM using CDP
		selected_value_result = await cdp_session.cdp_client.send.Runtime.evaluate(
			params={'expression': "document.getElementById('test-dropdown').value"}, session_id=cdp_session.session_id
		)
		selected_value = selected_value_result.get('result', {}).get('value')
		assert selected_value == 'option2'