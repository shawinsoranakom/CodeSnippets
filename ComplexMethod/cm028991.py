def test_www_subdomain_not_added_for_country_tlds(self):
		"""Test www subdomain is NOT automatically added for country-specific TLDs (2+ dots)."""
		from bubus import EventBus

		from browser_use.browser.watchdogs.security_watchdog import SecurityWatchdog

		# Test with country-specific TLDs - these should NOT get automatic www
		browser_profile = BrowserProfile(
			allowed_domains=['example.co.uk', 'test.com.au', 'site.co.jp'], headless=True, user_data_dir=None
		)
		browser_session = BrowserSession(browser_profile=browser_profile)
		event_bus = EventBus()
		watchdog = SecurityWatchdog(browser_session=browser_session, event_bus=event_bus)

		# Root domains should work exactly as specified
		assert watchdog._is_url_allowed('https://example.co.uk') is True
		assert watchdog._is_url_allowed('https://test.com.au') is True
		assert watchdog._is_url_allowed('https://site.co.jp') is True

		# www subdomains should NOT work automatically (user must specify explicitly)
		assert watchdog._is_url_allowed('https://www.example.co.uk') is False
		assert watchdog._is_url_allowed('https://www.test.com.au') is False
		assert watchdog._is_url_allowed('https://www.site.co.jp') is False

		# Other subdomains should not work
		assert watchdog._is_url_allowed('https://mail.example.co.uk') is False
		assert watchdog._is_url_allowed('https://api.test.com.au') is False