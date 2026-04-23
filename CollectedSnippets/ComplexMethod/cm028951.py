async def test_doctor_handle_returns_valid_structure():
	"""Test that doctor.handle() returns a valid result structure."""
	result = await doctor.handle()

	# Verify structure
	assert 'status' in result
	assert result['status'] in ('healthy', 'issues_found')
	assert 'checks' in result
	assert 'summary' in result

	# Verify all expected checks are present
	expected_checks = ['package', 'browser', 'network', 'cloudflared', 'profile_use']
	for check in expected_checks:
		assert check in result['checks']
		assert 'status' in result['checks'][check]
		assert 'message' in result['checks'][check]