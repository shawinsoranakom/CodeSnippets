def test_large_list_converts_to_set(self):
		"""Test that lists >= 100 items are converted to sets."""
		from bubus import EventBus

		from browser_use.browser.watchdogs.security_watchdog import SecurityWatchdog

		# Create a list of 100 domains
		large_list = [f'blocked{i}.com' for i in range(100)]

		browser_profile = BrowserProfile(prohibited_domains=large_list, headless=True, user_data_dir=None)
		browser_session = BrowserSession(browser_profile=browser_profile)
		event_bus = EventBus()
		watchdog = SecurityWatchdog(browser_session=browser_session, event_bus=event_bus)

		# Should be converted to set
		assert isinstance(browser_session.browser_profile.prohibited_domains, set)
		assert len(browser_session.browser_profile.prohibited_domains) == 100

		# Exact matches should work
		assert watchdog._is_url_allowed('https://blocked0.com') is False
		assert watchdog._is_url_allowed('https://blocked50.com') is False
		assert watchdog._is_url_allowed('https://blocked99.com') is False

		# Other domains should be allowed
		assert watchdog._is_url_allowed('https://example.com') is True
		assert watchdog._is_url_allowed('https://blocked100.com') is True