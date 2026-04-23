def test_match_url_with_domain_pattern():
	"""Test that the domain pattern matching utility works correctly"""

	# Test exact domain matches
	assert match_url_with_domain_pattern('https://example.com', 'example.com') is True
	assert match_url_with_domain_pattern('http://example.com', 'example.com') is False  # Default scheme is now https
	assert match_url_with_domain_pattern('https://google.com', 'example.com') is False

	# Test subdomain pattern matches
	assert match_url_with_domain_pattern('https://sub.example.com', '*.example.com') is True
	assert match_url_with_domain_pattern('https://example.com', '*.example.com') is True  # Base domain should match too
	assert match_url_with_domain_pattern('https://sub.sub.example.com', '*.example.com') is True
	assert match_url_with_domain_pattern('https://example.org', '*.example.com') is False

	# Test protocol pattern matches
	assert match_url_with_domain_pattern('https://example.com', 'http*://example.com') is True
	assert match_url_with_domain_pattern('http://example.com', 'http*://example.com') is True
	assert match_url_with_domain_pattern('ftp://example.com', 'http*://example.com') is False

	# Test explicit http protocol
	assert match_url_with_domain_pattern('http://example.com', 'http://example.com') is True
	assert match_url_with_domain_pattern('https://example.com', 'http://example.com') is False

	# Test Chrome extension pattern
	assert match_url_with_domain_pattern('chrome-extension://abcdefghijkl', 'chrome-extension://*') is True
	assert match_url_with_domain_pattern('chrome-extension://mnopqrstuvwx', 'chrome-extension://abcdefghijkl') is False

	# Test new tab page handling
	assert match_url_with_domain_pattern('about:blank', 'example.com') is False
	assert match_url_with_domain_pattern('about:blank', '*://*') is False
	assert match_url_with_domain_pattern('chrome://new-tab-page/', 'example.com') is False
	assert match_url_with_domain_pattern('chrome://new-tab-page/', '*://*') is False
	assert match_url_with_domain_pattern('chrome://new-tab-page', 'example.com') is False
	assert match_url_with_domain_pattern('chrome://new-tab-page', '*://*') is False