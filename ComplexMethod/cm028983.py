def test_url_components():
	"""Test handling of URL components like credentials, ports, fragments, etc."""

	# URLs with credentials (username:password@)
	assert match_url_with_domain_pattern('https://user:pass@example.com', 'example.com') is True
	assert match_url_with_domain_pattern('https://user:pass@example.com', '*.example.com') is True

	# URLs with ports
	assert match_url_with_domain_pattern('https://example.com:8080', 'example.com') is True
	assert match_url_with_domain_pattern('https://example.com:8080', 'example.com:8080') is True  # Port is stripped from pattern

	# URLs with paths
	assert match_url_with_domain_pattern('https://example.com/path/to/page', 'example.com') is True
	assert (
		match_url_with_domain_pattern('https://example.com/path/to/page', 'example.com/path') is False
	)  # Paths in patterns are not supported

	# URLs with query parameters
	assert match_url_with_domain_pattern('https://example.com?param=value', 'example.com') is True

	# URLs with fragments
	assert match_url_with_domain_pattern('https://example.com#section', 'example.com') is True

	# URLs with all components
	assert match_url_with_domain_pattern('https://user:pass@example.com:8080/path?query=val#fragment', 'example.com') is True