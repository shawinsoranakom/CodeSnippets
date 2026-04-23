def test_filter_sensitive_data(message_manager):
	"""Test that _filter_sensitive_data handles all sensitive data scenarios correctly"""
	# Set up a message with sensitive information
	message = UserMessage(content='My username is admin and password is secret123')

	# Case 1: No sensitive data provided
	message_manager.sensitive_data = None
	result = message_manager._filter_sensitive_data(message)
	assert result.content == 'My username is admin and password is secret123'

	# Case 2: All sensitive data is properly replaced
	message_manager.sensitive_data = {'username': 'admin', 'password': 'secret123'}
	result = message_manager._filter_sensitive_data(message)
	assert '<secret>username</secret>' in result.content
	assert '<secret>password</secret>' in result.content

	# Case 3: Make sure it works with nested content
	nested_message = UserMessage(content=[ContentPartTextParam(text='My username is admin and password is secret123')])
	result = message_manager._filter_sensitive_data(nested_message)
	assert '<secret>username</secret>' in result.content[0].text
	assert '<secret>password</secret>' in result.content[0].text

	# Case 4: Test with empty values
	message_manager.sensitive_data = {'username': 'admin', 'password': ''}
	result = message_manager._filter_sensitive_data(message)
	assert '<secret>username</secret>' in result.content
	# Only username should be replaced since password is empty

	# Case 5: Test with domain-specific sensitive data format
	message_manager.sensitive_data = {
		'example.com': {'username': 'admin', 'password': 'secret123'},
		'google.com': {'email': 'user@example.com', 'password': 'google_pass'},
	}
	# Update the message to include the values we're going to test
	message = UserMessage(content='My username is admin, email is user@example.com and password is secret123 or google_pass')
	result = message_manager._filter_sensitive_data(message)
	# All sensitive values should be replaced regardless of domain
	assert '<secret>username</secret>' in result.content
	assert '<secret>password</secret>' in result.content
	assert '<secret>email</secret>' in result.content