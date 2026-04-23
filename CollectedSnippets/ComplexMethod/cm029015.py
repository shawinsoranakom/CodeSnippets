async def test_background_tab_open_no_timeout(self, browser_session, base_url):
		"""Test that browser state doesn't timeout when a new tab opens in the background."""
		start_time = time.time()

		actions = [
			# Action 1: Navigate to home page
			f"""
			{{
				"thinking": "I'll navigate to the home page first",
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
			# Action 2: Open page1 in new background tab (stay on home page)
			f"""
			{{
				"thinking": "I'll open page1 in a new background tab",
				"evaluation_previous_goal": "Home page loaded",
				"memory": "Opening background tab",
				"next_goal": "Open background tab without switching to it",
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
			# Action 3: Immediately check browser state after background tab opens
			"""
			{
				"thinking": "After opening background tab, browser state should still be accessible",
				"evaluation_previous_goal": "Background tab opened",
				"memory": "Verifying browser state works",
				"next_goal": "Complete task",
				"action": [
					{
						"done": {
							"text": "Successfully opened background tab, browser state remains accessible",
							"success": true
						}
					}
				]
			}
			""",
		]

		mock_llm = create_mock_llm(actions=actions)

		agent = Agent(
			task=f'Navigate to {base_url}/home and open {base_url}/page1 in a new tab',
			llm=mock_llm,
			browser_session=browser_session,
		)

		# Run with timeout - this tests if browser state times out when new tabs open
		try:
			history = await asyncio.wait_for(agent.run(max_steps=3), timeout=120)
			elapsed = time.time() - start_time

			print(f'\n⏱️  Test completed in {elapsed:.2f} seconds')
			print(f'📊 Completed {len(history)} steps')

			# Verify each step has browser state (the key test - no timeouts)
			for i, step in enumerate(history.history):
				assert step.state is not None, f'Step {i} should have browser state'
				assert step.state.url is not None, f'Step {i} should have URL in browser state'
				print(f'  Step {i + 1}: URL={step.state.url}, tabs={len(step.state.tabs) if step.state.tabs else 0}')

			assert len(history) >= 2, 'Agent should have completed at least 2 steps'

			# Verify agent completed successfully
			final_result = history.final_result()
			assert final_result is not None, 'Agent should return a final result'
			assert 'Successfully' in final_result, 'Agent should report success'

			# Verify we have at least 2 tabs
			tabs = await browser_session.get_tabs()
			print(f'  Final tab count: {len(tabs)}')
			assert len(tabs) >= 2, f'Should have at least 2 tabs after opening background tab, got {len(tabs)}'

		except TimeoutError:
			pytest.fail('Test timed out after 2 minutes - browser state timed out after opening background tab')