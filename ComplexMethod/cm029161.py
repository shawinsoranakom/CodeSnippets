async def test_single_step_parametrized(llm_class, model_name):
	"""Test single step with different LLM providers using pytest parametrize."""
	if isinstance(model_name, dict):
		# Handle ChatOCIRaw which requires keyword arguments
		llm = llm_class(**model_name)
	else:
		llm = llm_class(model=model_name)

	agent = Agent(task='Click the button on the page', llm=llm)

	# Create temporary directory that will stay alive during the test
	with tempfile.TemporaryDirectory() as temp_dir:
		# Create mock state message
		mock_message = create_mock_state_message(temp_dir)

		agent.message_manager._set_message_with_type(mock_message, 'state')

		messages = agent.message_manager.get_messages()

		# Test with simple question
		response = await llm.ainvoke(messages, agent.AgentOutput)

		# Additional validation for OCI Raw
		if ChatOCIRaw is not None and isinstance(llm, ChatOCIRaw):
			# Verify OCI Raw generates proper Agent actions
			assert response.completion.action is not None
			assert len(response.completion.action) > 0

		# Basic assertions to ensure response is valid
		assert response.completion is not None
		assert response.usage is not None
		assert response.usage.total_tokens > 0