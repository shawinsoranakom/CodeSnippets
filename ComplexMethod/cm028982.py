def test_malformed_urls_and_patterns():
	"""Test handling of malformed URLs or patterns"""

	# Malformed URLs
	assert match_url_with_domain_pattern('not-a-url', 'example.com') is False
	assert match_url_with_domain_pattern('http://', 'example.com') is False
	assert match_url_with_domain_pattern('https://', 'example.com') is False
	assert match_url_with_domain_pattern('ftp:/example.com', 'example.com') is False  # Missing slash

	# Empty URLs or patterns
	assert match_url_with_domain_pattern('', 'example.com') is False
	assert match_url_with_domain_pattern('https://example.com', '') is False

	# URLs with no hostname
	assert match_url_with_domain_pattern('file:///path/to/file.txt', 'example.com') is False

	# Invalid pattern formats
	assert match_url_with_domain_pattern('https://example.com', '..example.com') is False
	assert match_url_with_domain_pattern('https://example.com', '.*.example.com') is False
	assert match_url_with_domain_pattern('https://example.com', '**') is False

	# Nested URL attacks in path, query or fragments
	assert match_url_with_domain_pattern('https://example.com/redirect?url=https://evil.com', 'example.com') is True
	assert match_url_with_domain_pattern('https://example.com/path/https://evil.com', 'example.com') is True
	assert match_url_with_domain_pattern('https://example.com#https://evil.com', 'example.com') is True
	# These should match example.com, not evil.com since urlparse extracts the hostname correctly

	# Complex URL obfuscation attempts
	assert match_url_with_domain_pattern('https://example.com/path?next=//evil.com/attack', 'example.com') is True
	assert match_url_with_domain_pattern('https://example.com@evil.com', 'example.com') is False
	assert match_url_with_domain_pattern('https://evil.com?example.com', 'example.com') is False
	assert match_url_with_domain_pattern('https://user:example.com@evil.com', 'example.com') is False