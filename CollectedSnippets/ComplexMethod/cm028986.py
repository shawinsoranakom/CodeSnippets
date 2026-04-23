def test_sensitive_data_filtered_from_action_results():
	"""
	Test that sensitive data in action results is filtered before being sent to the LLM.

	This tests the full flow:
	1. Agent outputs actions with <secret>password</secret> placeholder
	2. Placeholder gets replaced with real value 'secret_pass123' during action execution
	3. Action result contains: "Typed 'secret_pass123' into password field"
	4. When state messages are created, the real value should be replaced back to placeholder
	5. The LLM should never see the real password value
	"""
	import os
	import tempfile
	import uuid

	base_tmp = tempfile.gettempdir()
	file_system_path = os.path.join(base_tmp, str(uuid.uuid4()))

	sensitive_data: dict[str, str | dict[str, str]] = {'username': 'admin_user', 'password': 'secret_pass123'}

	message_manager = MessageManager(
		task='Login to the website',
		system_message=SystemMessage(content='You are a browser automation agent'),
		state=MessageManagerState(),
		file_system=FileSystem(file_system_path),
		sensitive_data=sensitive_data,
	)

	# Create browser state
	dom_state = SerializedDOMState(_root=None, selector_map={})
	browser_state = BrowserStateSummary(
		dom_state=dom_state,
		url='https://example.com/login',
		title='Login Page',
		tabs=[],
	)

	# Simulate action result containing sensitive data after placeholder replacement
	# This represents what happens after typing a password into a form field
	action_results = [
		ActionResult(
			long_term_memory="Successfully typed 'secret_pass123' into the password field",
			error=None,
		)
	]

	# Create model output for step 1
	model_output = AgentOutput(
		evaluation_previous_goal='Navigated to login page',
		memory='On login page, need to enter credentials',
		next_goal='Submit login form',
		action=[],
	)

	step_info = AgentStepInfo(step_number=1, max_steps=10)

	# Create state messages - this should filter sensitive data
	message_manager.create_state_messages(
		browser_state_summary=browser_state,
		model_output=model_output,
		result=action_results,
		step_info=step_info,
		use_vision=False,
	)

	# Get messages that would be sent to LLM
	messages = message_manager.get_messages()

	# Extract all text content from messages
	all_text = []
	for msg in messages:
		if isinstance(msg.content, str):
			all_text.append(msg.content)
		elif isinstance(msg.content, list):
			for part in msg.content:
				if isinstance(part, ContentPartTextParam):
					all_text.append(part.text)

	combined_text = '\n'.join(all_text)

	# Verify the bug is fixed: plaintext password should NOT appear in messages
	assert 'secret_pass123' not in combined_text, (
		'Sensitive data leaked! Real password value found in LLM messages. '
		'The _filter_sensitive_data method should replace it with <secret>password</secret>'
	)

	# Verify the filtered placeholder IS present (proves filtering happened)
	assert '<secret>password</secret>' in combined_text, (
		'Filtering did not work correctly. Expected <secret>password</secret> placeholder in messages.'
	)