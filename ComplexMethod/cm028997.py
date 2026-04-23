def test_allowed_domains_with_sets(self):
		"""Test that allowed_domains also works with set optimization."""
		from bubus import EventBus

		from browser_use.browser.watchdogs.security_watchdog import SecurityWatchdog

		# Create a large allowlist
		large_list = [f'allowed{i}.com' for i in range(100)]

		browser_profile = BrowserProfile(allowed_domains=large_list, headless=True, user_data_dir=None)
		browser_session = BrowserSession(browser_profile=browser_profile)
		event_bus = EventBus()
		watchdog = SecurityWatchdog(browser_session=browser_session, event_bus=event_bus)

		# Should be converted to set
		assert isinstance(browser_session.browser_profile.allowed_domains, set)

		# Allowed domains should work
		assert watchdog._is_url_allowed('https://allowed0.com') is True
		assert watchdog._is_url_allowed('https://www.allowed0.com') is True
		assert watchdog._is_url_allowed('https://allowed99.com') is True

		# Other domains should be blocked
		assert watchdog._is_url_allowed('https://example.com') is False
		assert watchdog._is_url_allowed('https://notallowed.com') is False