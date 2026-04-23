def test_replace_sensitive_data_with_missing_keys(registry, caplog):
	"""Test that _replace_sensitive_data handles missing keys gracefully"""
	# Create a simple Pydantic model with sensitive data placeholders
	params = SensitiveParams(text='Please enter <secret>username</secret> and <secret>password</secret>')

	# Case 1: All keys present - both placeholders should be replaced
	sensitive_data = {'username': 'user123', 'password': 'pass456'}
	result = registry._replace_sensitive_data(params, sensitive_data)
	assert result.text == 'Please enter user123 and pass456'
	assert '<secret>' not in result.text  # No secret tags should remain

	# Case 2: One key missing - only available key should be replaced
	sensitive_data = {'username': 'user123'}  # password is missing
	result = registry._replace_sensitive_data(params, sensitive_data)
	assert result.text == 'Please enter user123 and <secret>password</secret>'
	assert 'user123' in result.text
	assert '<secret>password</secret>' in result.text  # Missing key's tag remains

	# Case 3: Multiple keys missing - all tags should be preserved
	sensitive_data = {}  # both keys missing
	result = registry._replace_sensitive_data(params, sensitive_data)
	assert result.text == 'Please enter <secret>username</secret> and <secret>password</secret>'
	assert '<secret>username</secret>' in result.text
	assert '<secret>password</secret>' in result.text

	# Case 4: One key empty - empty values are treated as missing
	sensitive_data = {'username': 'user123', 'password': ''}
	result = registry._replace_sensitive_data(params, sensitive_data)
	assert result.text == 'Please enter user123 and <secret>password</secret>'
	assert 'user123' in result.text
	assert '<secret>password</secret>' in result.text