def test_sensitive_data_filtered_with_domain_specific_format():
	"""Test that domain-specific sensitive data format is also filtered from action results."""
	import os
	import tempfile
	import uuid

	base_tmp = tempfile.gettempdir()
	file_system_path = os.path.join(base_tmp, str(uuid.uuid4()))

	# Use domain-specific format
	sensitive_data: dict[str, str | dict[str, str]] = {
		'example.com': {'api_key': 'sk-secret-api-key-12345'},
	}

	message_manager = MessageManager(
		task='Use the API',
		system_message=SystemMessage(content='You are a browser automation agent'),
		state=MessageManagerState(),
		file_system=FileSystem(file_system_path),
		sensitive_data=sensitive_data,
	)

	dom_state = SerializedDOMState(_root=None, selector_map={})
	browser_state = BrowserStateSummary(
		dom_state=dom_state,
		url='https://example.com/api',
		title='API Page',
		tabs=[],
	)

	# Action result with API key that should be filtered
	action_results = [
		ActionResult(
			long_term_memory="Set API key to 'sk-secret-api-key-12345' in the input field",
			error=None,
		)
	]

	model_output = AgentOutput(
		evaluation_previous_goal='Opened API settings',
		memory='Need to configure API key',
		next_goal='Save settings',
		action=[],
	)

	step_info = AgentStepInfo(step_number=1, max_steps=10)

	message_manager.create_state_messages(
		browser_state_summary=browser_state,
		model_output=model_output,
		result=action_results,
		step_info=step_info,
		use_vision=False,
	)

	messages = message_manager.get_messages()

	all_text = []
	for msg in messages:
		if isinstance(msg.content, str):
			all_text.append(msg.content)
		elif isinstance(msg.content, list):
			for part in msg.content:
				if isinstance(part, ContentPartTextParam):
					all_text.append(part.text)

	combined_text = '\n'.join(all_text)

	# API key should be filtered out
	assert 'sk-secret-api-key-12345' not in combined_text, 'API key leaked into LLM messages!'
	assert '<secret>api_key</secret>' in combined_text, 'API key placeholder not found in messages'