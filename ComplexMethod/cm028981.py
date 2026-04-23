def test_unsafe_domain_patterns():
	"""Test that unsafe domain patterns are rejected"""

	# These are unsafe patterns that could match too many domains
	assert match_url_with_domain_pattern('https://evil.com', '*google.com') is False
	assert match_url_with_domain_pattern('https://google.com.evil.com', '*.*.com') is False
	assert match_url_with_domain_pattern('https://google.com', '**google.com') is False
	assert match_url_with_domain_pattern('https://google.com', 'g*e.com') is False
	assert match_url_with_domain_pattern('https://google.com', '*com*') is False

	# Test with patterns that have multiple asterisks in different positions
	assert match_url_with_domain_pattern('https://subdomain.example.com', '*domain*example*') is False
	assert match_url_with_domain_pattern('https://sub.domain.example.com', '*.*.example.com') is False

	# Test patterns with wildcards in TLD part
	assert match_url_with_domain_pattern('https://example.com', 'example.*') is False
	assert match_url_with_domain_pattern('https://example.org', 'example.*') is False