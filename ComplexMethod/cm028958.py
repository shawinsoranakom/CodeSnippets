def test_detect_variables_multiple_types():
	"""Test detection of multiple variable types in one history"""
	history = create_mock_history(
		[
			({'input': {'index': 1, 'text': 'test@example.com'}}, create_test_element(attributes={'type': 'email'})),
			({'input': {'index': 2, 'text': 'John'}}, create_test_element(attributes={'name': 'first_name'})),
			({'input': {'index': 3, 'text': '1990-01-01'}}, create_test_element(attributes={'type': 'date'})),
		]
	)

	result = detect_variables_in_history(history)  # type: ignore[arg-type]

	assert len(result) == 3
	assert 'email' in result
	assert 'first_name' in result
	assert 'date' in result

	assert result['email'].original_value == 'test@example.com'
	assert result['first_name'].original_value == 'John'
	assert result['date'].original_value == '1990-01-01'