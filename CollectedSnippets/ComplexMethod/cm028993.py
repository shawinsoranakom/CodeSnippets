def test_simple_prohibited_domains(self):
		"""Domain-only patterns block exact host and www, but not other subdomains."""
		from bubus import EventBus

		from browser_use.browser.watchdogs.security_watchdog import SecurityWatchdog

		browser_profile = BrowserProfile(prohibited_domains=['example.com', 'test.org'], headless=True, user_data_dir=None)
		browser_session = BrowserSession(browser_profile=browser_profile)
		event_bus = EventBus()
		watchdog = SecurityWatchdog(browser_session=browser_session, event_bus=event_bus)

		# Block exact and www
		assert watchdog._is_url_allowed('https://example.com') is False
		assert watchdog._is_url_allowed('https://www.example.com') is False
		assert watchdog._is_url_allowed('https://test.org') is False
		assert watchdog._is_url_allowed('https://www.test.org') is False

		# Allow other subdomains when only root is prohibited
		assert watchdog._is_url_allowed('https://mail.example.com') is True
		assert watchdog._is_url_allowed('https://api.test.org') is True

		# Allow unrelated domains
		assert watchdog._is_url_allowed('https://notexample.com') is True