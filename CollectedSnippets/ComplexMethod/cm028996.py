def test_www_variant_matching_with_sets(self):
		"""Test that www variants are checked in set-based lookups."""
		from bubus import EventBus

		from browser_use.browser.watchdogs.security_watchdog import SecurityWatchdog

		# Create a list with 100 domains (some with www, some without)
		large_list = [f'site{i}.com' for i in range(50)] + [f'www.domain{i}.org' for i in range(50)]

		browser_profile = BrowserProfile(prohibited_domains=large_list, headless=True, user_data_dir=None)
		browser_session = BrowserSession(browser_profile=browser_profile)
		event_bus = EventBus()
		watchdog = SecurityWatchdog(browser_session=browser_session, event_bus=event_bus)

		# Should be converted to set
		assert isinstance(browser_session.browser_profile.prohibited_domains, set)

		# Test www variant matching for domains without www prefix
		assert watchdog._is_url_allowed('https://site0.com') is False
		assert watchdog._is_url_allowed('https://www.site0.com') is False  # Should also be blocked

		# Test www variant matching for domains with www prefix
		assert watchdog._is_url_allowed('https://www.domain0.org') is False
		assert watchdog._is_url_allowed('https://domain0.org') is False  # Should also be blocked

		# Test that unrelated domains are allowed
		assert watchdog._is_url_allowed('https://example.com') is True
		assert watchdog._is_url_allowed('https://www.example.com') is True