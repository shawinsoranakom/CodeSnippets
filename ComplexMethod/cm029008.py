async def test_agent_screenshot_with_vision_enabled(browser_session, base_url):
	"""Test that agent captures screenshots when vision is enabled.

	This integration test verifies that:
	1. Agent with vision=True navigates to a page
	2. After prepare_context/update message manager, screenshot is captured
	3. Screenshot is included in the agent's history state
	"""

	# Create mock LLM actions
	actions = [
		f"""
		{{
			"thinking": "I'll navigate to the screenshot test page",
			"evaluation_previous_goal": "Starting task",
			"memory": "Navigating to page",
			"next_goal": "Navigate to test page",
			"action": [
				{{
					"navigate": {{
						"url": "{base_url}/screenshot-page",
						"new_tab": false
					}}
				}}
			]
		}}
		""",
		"""
		{
			"thinking": "Page loaded, completing task",
			"evaluation_previous_goal": "Page loaded",
			"memory": "Task completed",
			"next_goal": "Complete task",
			"action": [
				{
					"done": {
						"text": "Successfully navigated and captured screenshot",
						"success": true
					}
				}
			]
		}
		""",
	]

	mock_llm = create_mock_llm(actions=actions)

	# Create agent with vision enabled
	agent = Agent(
		task=f'Navigate to {base_url}/screenshot-page',
		llm=mock_llm,
		browser_session=browser_session,
		use_vision=True,  # Enable vision/screenshots
	)

	# Run agent
	history = await agent.run(max_steps=2)

	# Verify agent completed successfully
	assert len(history) >= 1, 'Agent should have completed at least 1 step'
	final_result = history.final_result()
	assert final_result is not None, 'Agent should return a final result'

	# Verify screenshots were captured in the history
	screenshot_found = False
	for i, step in enumerate(history.history):
		# Check if browser state has screenshot path
		if step.state and hasattr(step.state, 'screenshot_path') and step.state.screenshot_path:
			screenshot_found = True
			print(f'\n✅ Step {i + 1}: Screenshot captured at {step.state.screenshot_path}')

			# Verify screenshot file exists (it should be saved to disk)
			import os

			assert os.path.exists(step.state.screenshot_path), f'Screenshot file should exist at {step.state.screenshot_path}'

			# Verify screenshot file has content
			screenshot_size = os.path.getsize(step.state.screenshot_path)
			assert screenshot_size > 0, f'Screenshot file should have content, got {screenshot_size} bytes'
			print(f'   Screenshot size: {screenshot_size} bytes')

	assert screenshot_found, 'At least one screenshot should be captured when vision is enabled'

	print('\n🎉 Integration test passed: Screenshots are captured correctly with vision enabled')