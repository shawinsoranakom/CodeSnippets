def test_small_list_keeps_pattern_support(self):
		"""Test that lists < 100 items keep pattern matching support."""
		from bubus import EventBus

		from browser_use.browser.watchdogs.security_watchdog import SecurityWatchdog

		browser_profile = BrowserProfile(
			prohibited_domains=['*.google.com', 'x.com', 'facebook.com'], headless=True, user_data_dir=None
		)
		browser_session = BrowserSession(browser_profile=browser_profile)
		event_bus = EventBus()
		watchdog = SecurityWatchdog(browser_session=browser_session, event_bus=event_bus)

		# Should still be a list
		assert isinstance(browser_session.browser_profile.prohibited_domains, list)

		# Pattern matching should work
		assert watchdog._is_url_allowed('https://www.google.com') is False
		assert watchdog._is_url_allowed('https://mail.google.com') is False
		assert watchdog._is_url_allowed('https://google.com') is False

		# Exact matches should work
		assert watchdog._is_url_allowed('https://x.com') is False
		assert watchdog._is_url_allowed('https://facebook.com') is False

		# Other domains should be allowed
		assert watchdog._is_url_allowed('https://example.com') is True