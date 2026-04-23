def test_is_url_allowed(self):
		"""
		Test the _is_url_allowed method to verify that it correctly checks URLs against
		the allowed domains configuration.
		"""
		# Scenario 1: allowed_domains is None, any URL should be allowed.
		from bubus import EventBus

		from browser_use.browser.watchdogs.security_watchdog import SecurityWatchdog

		config1 = BrowserProfile(allowed_domains=None, headless=True, user_data_dir=None)
		context1 = BrowserSession(browser_profile=config1)
		event_bus1 = EventBus()
		watchdog1 = SecurityWatchdog(browser_session=context1, event_bus=event_bus1)
		assert watchdog1._is_url_allowed('http://anydomain.com') is True
		assert watchdog1._is_url_allowed('https://anotherdomain.org/path') is True

		# Scenario 2: allowed_domains is provided.
		# Note: match_url_with_domain_pattern defaults to https:// scheme when none is specified
		allowed = ['https://example.com', 'http://example.com', 'http://*.mysite.org', 'https://*.mysite.org']
		config2 = BrowserProfile(allowed_domains=allowed, headless=True, user_data_dir=None)
		context2 = BrowserSession(browser_profile=config2)
		event_bus2 = EventBus()
		watchdog2 = SecurityWatchdog(browser_session=context2, event_bus=event_bus2)

		# URL exactly matching
		assert watchdog2._is_url_allowed('http://example.com') is True
		# URL with subdomain (should not be allowed)
		assert watchdog2._is_url_allowed('http://sub.example.com/path') is False
		# URL with subdomain for wildcard pattern (should be allowed)
		assert watchdog2._is_url_allowed('http://sub.mysite.org') is True
		# URL that matches second allowed domain
		assert watchdog2._is_url_allowed('https://mysite.org/page') is True
		# URL with port number, still allowed (port is stripped)
		assert watchdog2._is_url_allowed('http://example.com:8080') is True
		assert watchdog2._is_url_allowed('https://example.com:443') is True

		# Scenario 3: Malformed URL or empty domain
		# urlparse will return an empty netloc for some malformed URLs.
		assert watchdog2._is_url_allowed('notaurl') is False