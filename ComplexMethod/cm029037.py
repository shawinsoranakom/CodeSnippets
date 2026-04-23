def test_complete_url_shortening_pipeline(self, agent: Agent):
		"""Test the complete pipeline: input shortening -> processing -> output restoration."""

		# Step 1: Input processing with URL shortening
		original_content = f'Navigate to {SUPER_LONG_URL} and extract the API documentation'

		messages: list[BaseMessage] = [UserMessage(content=original_content)]

		url_mappings = agent._process_messsages_and_replace_long_urls_shorter_ones(messages)

		# Verify URL was shortened in input
		assert len(url_mappings) == 1
		shortened_url = next(iter(url_mappings.keys()))
		assert url_mappings[shortened_url] == SUPER_LONG_URL
		assert shortened_url in (messages[0].content or '')

		# Step 2: Simulate agent output with shortened URL
		output_json = {
			'thinking': f'I will navigate to {shortened_url} to get the documentation',
			'evaluation_previous_goal': 'Starting documentation extraction',
			'memory': f'Target URL: {shortened_url}',
			'next_goal': 'Extract API documentation',
			'action': [{'navigate': {'url': shortened_url, 'new_tab': True}}],
		}

		# Create AgentOutput with custom actions
		tools = agent.tools
		ActionModel = tools.registry.create_action_model()
		AgentOutputWithActions = AgentOutput.type_with_custom_actions(ActionModel)
		agent_output = AgentOutputWithActions.model_validate_json(json.dumps(output_json))

		# Step 3: Output processing with URL restoration (modifies agent_output in-place)
		agent._recursive_process_all_strings_inside_pydantic_model(agent_output, url_mappings)

		# Verify complete pipeline worked correctly
		assert SUPER_LONG_URL in (agent_output.thinking or '')
		assert SUPER_LONG_URL in (agent_output.memory or '')
		action_data = agent_output.action[0].model_dump()
		assert action_data['navigate']['url'] == SUPER_LONG_URL
		assert action_data['navigate']['new_tab'] is True

		# Verify original shortened content is no longer present
		assert shortened_url not in (agent_output.thinking or '')
		assert shortened_url not in (agent_output.memory or '')