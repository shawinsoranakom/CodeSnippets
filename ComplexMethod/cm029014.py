async def test_create_and_switch_three_tabs(self, browser_session, base_url):
		"""Test that agent can create 3 tabs, switch between them, and call done().

		This test verifies that browser state is retrieved between each step.
		"""
		start_time = time.time()

		actions = [
			# Action 1: Navigate to home page
			f"""
			{{
				"thinking": "I'll start by navigating to the home page",
				"evaluation_previous_goal": "Starting task",
				"memory": "Navigating to home page",
				"next_goal": "Navigate to home page",
				"action": [
					{{
						"navigate": {{
							"url": "{base_url}/home",
							"new_tab": false
						}}
					}}
				]
			}}
			""",
			# Action 2: Open page1 in new tab
			f"""
			{{
				"thinking": "Now I'll open page 1 in a new tab",
				"evaluation_previous_goal": "Home page loaded",
				"memory": "Opening page 1 in new tab",
				"next_goal": "Open page 1 in new tab",
				"action": [
					{{
						"navigate": {{
							"url": "{base_url}/page1",
							"new_tab": true
						}}
					}}
				]
			}}
			""",
			# Action 3: Open page2 in new tab
			f"""
			{{
				"thinking": "Now I'll open page 2 in a new tab",
				"evaluation_previous_goal": "Page 1 opened in new tab",
				"memory": "Opening page 2 in new tab",
				"next_goal": "Open page 2 in new tab",
				"action": [
					{{
						"navigate": {{
							"url": "{base_url}/page2",
							"new_tab": true
						}}
					}}
				]
			}}
			""",
			# Action 4: Switch to first tab
			"""
			{
				"thinking": "Now I'll switch back to the first tab",
				"evaluation_previous_goal": "Page 2 opened in new tab",
				"memory": "Switching to first tab",
				"next_goal": "Switch to first tab",
				"action": [
					{
						"switch": {
							"tab_id": "0000"
						}
					}
				]
			}
			""",
			# Action 5: Done
			"""
			{
				"thinking": "I've successfully created 3 tabs and switched between them",
				"evaluation_previous_goal": "Switched to first tab",
				"memory": "All tabs created and switched",
				"next_goal": "Complete task",
				"action": [
					{
						"done": {
							"text": "Successfully created 3 tabs and switched between them",
							"success": true
						}
					}
				]
			}
			""",
		]

		mock_llm = create_mock_llm(actions=actions)

		agent = Agent(
			task=f'Navigate to {base_url}/home, then open {base_url}/page1 and {base_url}/page2 in new tabs, then switch back to the first tab',
			llm=mock_llm,
			browser_session=browser_session,
		)

		# Run with timeout - should complete within 2 minutes
		try:
			history = await asyncio.wait_for(agent.run(max_steps=5), timeout=120)
			elapsed = time.time() - start_time

			print(f'\n⏱️  Test completed in {elapsed:.2f} seconds')
			print(f'📊 Completed {len(history)} steps')

			# Verify each step has browser state
			for i, step in enumerate(history.history):
				assert step.state is not None, f'Step {i} should have browser state'
				assert step.state.url is not None, f'Step {i} should have URL in browser state'
				print(f'  Step {i + 1}: URL={step.state.url}, tabs={len(step.state.tabs) if step.state.tabs else 0}')

			assert len(history) >= 4, 'Agent should have completed at least 4 steps'

			# Verify we have 3 tabs open
			tabs = await browser_session.get_tabs()
			assert len(tabs) >= 3, f'Should have at least 3 tabs open, got {len(tabs)}'

			# Verify agent completed successfully
			final_result = history.final_result()
			assert final_result is not None, 'Agent should return a final result'
			assert 'Successfully' in final_result, 'Agent should report success'

			# Note: Test is fast (< 1s) because mock LLM returns instantly and pages are simple,
			# but browser state IS being retrieved correctly between steps as verified above
		except TimeoutError:
			pytest.fail('Test timed out after 2 minutes - agent hung during tab operations')