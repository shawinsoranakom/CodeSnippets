def test_is_root_domain_helper(self):
		"""Test the _is_root_domain helper method logic."""
		from bubus import EventBus

		from browser_use.browser.watchdogs.security_watchdog import SecurityWatchdog

		browser_profile = BrowserProfile(allowed_domains=['example.com'], headless=True, user_data_dir=None)
		browser_session = BrowserSession(browser_profile=browser_profile)
		event_bus = EventBus()
		watchdog = SecurityWatchdog(browser_session=browser_session, event_bus=event_bus)

		# Simple root domains (1 dot) - should return True
		assert watchdog._is_root_domain('example.com') is True
		assert watchdog._is_root_domain('test.org') is True
		assert watchdog._is_root_domain('site.net') is True

		# Subdomains (more than 1 dot) - should return False
		assert watchdog._is_root_domain('www.example.com') is False
		assert watchdog._is_root_domain('mail.example.com') is False
		assert watchdog._is_root_domain('example.co.uk') is False
		assert watchdog._is_root_domain('test.com.au') is False

		# Wildcards - should return False
		assert watchdog._is_root_domain('*.example.com') is False
		assert watchdog._is_root_domain('*example.com') is False

		# Full URLs - should return False
		assert watchdog._is_root_domain('https://example.com') is False
		assert watchdog._is_root_domain('http://test.org') is False

		# Invalid domains - should return False
		assert watchdog._is_root_domain('example') is False
		assert watchdog._is_root_domain('') is False