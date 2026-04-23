def _is_url_match(self, url: str, host: str, scheme: str, pattern: str) -> bool:
		"""Check if a URL matches a pattern."""

		# Full URL for matching (scheme + host)
		full_url_pattern = f'{scheme}://{host}'

		# Handle glob patterns
		if '*' in pattern:
			self._log_glob_warning()
			import fnmatch

			# Check if pattern matches the host
			if pattern.startswith('*.'):
				# Pattern like *.example.com should match subdomains and main domain
				domain_part = pattern[2:]  # Remove *.
				if host == domain_part or host.endswith('.' + domain_part):
					# Only match http/https URLs for domain-only patterns
					if scheme in ['http', 'https']:
						return True
			elif pattern.endswith('/*'):
				# Pattern like brave://* or http*://example.com/*
				if fnmatch.fnmatch(url, pattern):
					return True
			else:
				# Use fnmatch for other glob patterns
				if fnmatch.fnmatch(
					full_url_pattern if '://' in pattern else host,
					pattern,
				):
					return True
		else:
			# Exact match
			if '://' in pattern:
				# Full URL pattern
				if url.startswith(pattern):
					return True
			else:
				# Domain-only pattern (case-insensitive comparison)
				if host.lower() == pattern.lower():
					return True
				# If pattern is a root domain, also check www subdomain
				if self._is_root_domain(pattern) and host.lower() == f'www.{pattern.lower()}':
					return True

		return False