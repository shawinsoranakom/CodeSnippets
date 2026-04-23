async def test_plan_generation_from_plan_update(browser_session, mock_llm):
	agent = _make_agent(browser_session, mock_llm)
	output = _make_agent_output(plan_update=['Navigate to page', 'Search for item', 'Extract price'])

	agent._update_plan_from_model_output(output)

	assert agent.state.plan is not None
	assert len(agent.state.plan) == 3
	assert agent.state.plan[0].status == 'current'
	assert agent.state.plan[1].status == 'pending'
	assert agent.state.plan[2].status == 'pending'
	assert agent.state.current_plan_item_index == 0
	assert agent.state.plan_generation_step == agent.state.n_steps