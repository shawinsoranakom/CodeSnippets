def _is_url_allowed(self, url: str) -> bool:
		"""Check if a URL is allowed based on the allowed_domains configuration.

		Args:
			url: The URL to check

		Returns:
			True if the URL is allowed, False otherwise
		"""

		# Always allow internal browser targets (before any other checks)
		if url in ['about:blank', 'chrome://new-tab-page/', 'chrome://new-tab-page', 'chrome://newtab/']:
			return True

		# Parse the URL to extract components
		from urllib.parse import urlparse

		try:
			parsed = urlparse(url)
		except Exception:
			# Invalid URL
			return False

		# Allow data: and blob: URLs (they don't have hostnames)
		if parsed.scheme in ['data', 'blob']:
			return True

		# Get the actual host (domain)
		host = parsed.hostname
		if not host:
			return False

		# Check if IP addresses should be blocked (before domain checks)
		if self.browser_session.browser_profile.block_ip_addresses:
			if self._is_ip_address(host):
				return False

		# If no allowed_domains specified, allow all URLs
		if (
			not self.browser_session.browser_profile.allowed_domains
			and not self.browser_session.browser_profile.prohibited_domains
		):
			return True

		# Check allowed domains (fast path for sets, slow path for lists with patterns)
		if self.browser_session.browser_profile.allowed_domains:
			allowed_domains = self.browser_session.browser_profile.allowed_domains

			if isinstance(allowed_domains, set):
				# Fast path: O(1) exact hostname match - check both www and non-www variants
				host_variant, host_alt = self._get_domain_variants(host)
				return host_variant in allowed_domains or host_alt in allowed_domains
			else:
				# Slow path: O(n) pattern matching for lists
				for pattern in allowed_domains:
					if self._is_url_match(url, host, parsed.scheme, pattern):
						return True
				return False

		# Check prohibited domains (fast path for sets, slow path for lists with patterns)
		if self.browser_session.browser_profile.prohibited_domains:
			prohibited_domains = self.browser_session.browser_profile.prohibited_domains

			if isinstance(prohibited_domains, set):
				# Fast path: O(1) exact hostname match - check both www and non-www variants
				host_variant, host_alt = self._get_domain_variants(host)
				return host_variant not in prohibited_domains and host_alt not in prohibited_domains
			else:
				# Slow path: O(n) pattern matching for lists
				for pattern in prohibited_domains:
					if self._is_url_match(url, host, parsed.scheme, pattern):
						return False
				return True

		return True