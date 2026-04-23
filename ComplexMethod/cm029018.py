async def test_dom_serializer_element_counts_detailed(self, browser_session, base_url):
		"""Detailed test to verify specific element types are captured correctly."""

		actions = [
			f"""
			{{
				"thinking": "Navigating to test page",
				"evaluation_previous_goal": "Starting",
				"memory": "Navigate",
				"next_goal": "Navigate",
				"action": [
					{{
						"navigate": {{
							"url": "{base_url}/dom-test-main",
							"new_tab": false
						}}
					}}
				]
			}}
			""",
			"""
			{
				"thinking": "Done",
				"evaluation_previous_goal": "Navigated",
				"memory": "Complete",
				"next_goal": "Done",
				"action": [
					{
						"done": {
							"text": "Done",
							"success": true
						}
					}
				]
			}
			""",
		]

		mock_llm = create_mock_llm(actions=actions)
		agent = Agent(
			task=f'Navigate to {base_url}/dom-test-main',
			llm=mock_llm,
			browser_session=browser_session,
		)

		history = await agent.run(max_steps=2)

		# Get current browser state to access selector_map
		browser_state_summary = await browser_session.get_browser_state_summary(
			include_screenshot=False,
			include_recent_events=False,
		)
		selector_map = browser_state_summary.dom_state.selector_map

		# Count different element types
		buttons = 0
		inputs = 0
		links = 0

		for idx, element in selector_map.items():
			element_str = str(element).lower()
			if 'button' in element_str or '<button' in element_str:
				buttons += 1
			elif 'input' in element_str or '<input' in element_str:
				inputs += 1
			elif 'link' in element_str or '<a' in element_str or 'href' in element_str:
				links += 1

		print('\n📊 Element Type Counts:')
		print(f'   Buttons: {buttons}')
		print(f'   Inputs: {inputs}')
		print(f'   Links: {links}')
		print(f'   Total: {len(selector_map)}')

		# We should have at least some of each type from the regular DOM
		assert buttons >= 1, f'Should find at least 1 button, found {buttons}'
		assert inputs >= 1, f'Should find at least 1 input, found {inputs}'

		print('\n✅ Element type verification passed!')