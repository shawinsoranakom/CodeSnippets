def test_automatic_www_subdomain_addition(self):
		"""Test that root domains automatically allow www subdomain."""
		from bubus import EventBus

		from browser_use.browser.watchdogs.security_watchdog import SecurityWatchdog

		# Test with simple root domains
		browser_profile = BrowserProfile(allowed_domains=['example.com', 'test.org'], headless=True, user_data_dir=None)
		browser_session = BrowserSession(browser_profile=browser_profile)
		event_bus = EventBus()
		watchdog = SecurityWatchdog(browser_session=browser_session, event_bus=event_bus)

		# Root domain should allow itself
		assert watchdog._is_url_allowed('https://example.com') is True
		assert watchdog._is_url_allowed('https://test.org') is True

		# Root domain should automatically allow www subdomain
		assert watchdog._is_url_allowed('https://www.example.com') is True
		assert watchdog._is_url_allowed('https://www.test.org') is True

		# Should not allow other subdomains
		assert watchdog._is_url_allowed('https://mail.example.com') is False
		assert watchdog._is_url_allowed('https://sub.test.org') is False

		# Should not allow unrelated domains
		assert watchdog._is_url_allowed('https://notexample.com') is False
		assert watchdog._is_url_allowed('https://www.notexample.com') is False