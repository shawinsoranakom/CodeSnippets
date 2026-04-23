def test_is_new_tab_page():
	"""Test is_new_tab_page function"""
	# Test about:blank
	assert is_new_tab_page('about:blank') is True

	# Test chrome://new-tab-page variations
	assert is_new_tab_page('chrome://new-tab-page/') is True
	assert is_new_tab_page('chrome://new-tab-page') is True

	# Test regular URLs
	assert is_new_tab_page('https://example.com') is False
	assert is_new_tab_page('http://google.com') is False
	assert is_new_tab_page('') is False
	assert is_new_tab_page('chrome://settings') is False