async def test_click_link_aborts_remaining(self, browser_session, base_url, tools):
		"""Click a link that navigates to another page — remaining actions skipped."""
		await tools.navigate(url=f'{base_url}/page_a', new_tab=False, browser_session=browser_session)
		await asyncio.sleep(0.5)

		# Get the selector map to find the link index
		state = await browser_session.get_browser_state_summary()
		assert state.dom_state is not None
		selector_map = state.dom_state.selector_map

		# Find the link element (a#link_b)
		link_index = None
		for idx, element in selector_map.items():
			if hasattr(element, 'tag_name') and element.tag_name == 'a':
				link_index = idx
				break

		assert link_index is not None, 'Could not find link element in selector map'

		ActionModel = tools.registry.create_action_model()
		actions = [
			ActionModel.model_validate({'click': {'index': link_index}}),
			ActionModel.model_validate({'scroll': {'down': True, 'pages': 1}}),
			ActionModel.model_validate({'scroll': {'down': True, 'pages': 1}}),
		]

		mock_llm = create_mock_llm()
		agent = Agent(task='test', llm=mock_llm, browser_session=browser_session, tools=tools)

		results = await agent.multi_act(actions)

		# Click navigated to page_b — runtime guard should stop at 1
		assert len(results) == 1, f'Expected 1 result but got {len(results)}: {results}'

		# Verify we're on page_b
		url = await browser_session.get_current_page_url()
		assert '/page_b' in url