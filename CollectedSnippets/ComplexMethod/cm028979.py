def test_simple_domain_specific_sensitive_data(registry, caplog):
	"""Test the basic functionality of domain-specific sensitive data replacement"""
	# Create a simple Pydantic model with sensitive data placeholders
	params = SensitiveParams(text='Please enter <secret>username</secret> and <secret>password</secret>')

	# Simple test with directly instantiable values
	sensitive_data = {
		'example.com': {'username': 'example_user'},
		'other_data': 'non_secret_value',  # Old format mixed with new
	}

	# Without a URL, domain-specific secrets should NOT be exposed
	result = registry._replace_sensitive_data(params, sensitive_data)
	assert result.text == 'Please enter <secret>username</secret> and <secret>password</secret>'
	assert '<secret>username</secret>' in result.text  # Should NOT be replaced without URL
	assert '<secret>password</secret>' in result.text  # Password is missing in sensitive_data
	assert 'example_user' not in result.text  # Domain-specific value should not appear

	# Test with a matching URL - domain-specific secrets should be exposed
	result = registry._replace_sensitive_data(params, sensitive_data, 'https://example.com/login')
	assert result.text == 'Please enter example_user and <secret>password</secret>'
	assert 'example_user' in result.text  # Should be replaced with matching URL
	assert '<secret>password</secret>' in result.text  # Password is still missing
	assert '<secret>username</secret>' not in result.text