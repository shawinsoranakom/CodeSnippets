def match_url_with_domain_pattern(url: str, domain_pattern: str, log_warnings: bool = False) -> bool:
	"""
	Check if a URL matches a domain pattern. SECURITY CRITICAL.

	Supports optional glob patterns and schemes:
	- *.example.com will match sub.example.com and example.com
	- *google.com will match google.com, agoogle.com, and www.google.com
	- http*://example.com will match http://example.com, https://example.com
	- chrome-extension://* will match chrome-extension://aaaaaaaaaaaa and chrome-extension://bbbbbbbbbbbbb

	When no scheme is specified, https is used by default for security.
	For example, 'example.com' will match 'https://example.com' but not 'http://example.com'.

	Note: New tab pages (about:blank, chrome://new-tab-page) must be handled at the callsite, not inside this function.

	Args:
		url: The URL to check
		domain_pattern: Domain pattern to match against
		log_warnings: Whether to log warnings about unsafe patterns

	Returns:
		bool: True if the URL matches the pattern, False otherwise
	"""
	try:
		# Note: new tab pages should be handled at the callsite, not here
		if is_new_tab_page(url):
			return False

		parsed_url = urlparse(url)

		# Extract only the hostname and scheme components
		scheme = parsed_url.scheme.lower() if parsed_url.scheme else ''
		domain = parsed_url.hostname.lower() if parsed_url.hostname else ''

		if not scheme or not domain:
			return False

		# Normalize the domain pattern
		domain_pattern = domain_pattern.lower()

		# Handle pattern with scheme
		if '://' in domain_pattern:
			pattern_scheme, pattern_domain = domain_pattern.split('://', 1)
		else:
			pattern_scheme = 'https'  # Default to matching only https for security
			pattern_domain = domain_pattern

		# Handle port in pattern (we strip ports from patterns since we already
		# extracted only the hostname from the URL)
		if ':' in pattern_domain and not pattern_domain.startswith(':'):
			pattern_domain = pattern_domain.split(':', 1)[0]

		# If scheme doesn't match, return False
		if not fnmatch(scheme, pattern_scheme):
			return False

		# Check for exact match
		if pattern_domain == '*' or domain == pattern_domain:
			return True

		# Handle glob patterns
		if '*' in pattern_domain:
			# Check for unsafe glob patterns
			# First, check for patterns like *.*.domain which are unsafe
			if pattern_domain.count('*.') > 1 or pattern_domain.count('.*') > 1:
				if log_warnings:
					logger = logging.getLogger(__name__)
					logger.error(f'⛔️ Multiple wildcards in pattern=[{domain_pattern}] are not supported')
				return False  # Don't match unsafe patterns

			# Check for wildcards in TLD part (example.*)
			if pattern_domain.endswith('.*'):
				if log_warnings:
					logger = logging.getLogger(__name__)
					logger.error(f'⛔️ Wildcard TLDs like in pattern=[{domain_pattern}] are not supported for security')
				return False  # Don't match unsafe patterns

			# Then check for embedded wildcards
			bare_domain = pattern_domain.replace('*.', '')
			if '*' in bare_domain:
				if log_warnings:
					logger = logging.getLogger(__name__)
					logger.error(f'⛔️ Only *.domain style patterns are supported, ignoring pattern=[{domain_pattern}]')
				return False  # Don't match unsafe patterns

			# Special handling so that *.google.com also matches bare google.com
			if pattern_domain.startswith('*.'):
				parent_domain = pattern_domain[2:]
				if domain == parent_domain or fnmatch(domain, parent_domain):
					return True

			# Normal case: match domain against pattern
			if fnmatch(domain, pattern_domain):
				return True

		return False
	except Exception as e:
		logger = logging.getLogger(__name__)
		logger.error(f'⛔️ Error matching URL {url} with pattern {domain_pattern}: {type(e).__name__}: {e}')
		return False