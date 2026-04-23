def test_glob_pattern_matching(self):
		"""Test that glob patterns in allowed_domains work correctly."""
		from bubus import EventBus

		from browser_use.browser.watchdogs.security_watchdog import SecurityWatchdog

		# Test *.example.com pattern (should match subdomains and main domain)
		browser_profile = BrowserProfile(allowed_domains=['*.example.com'], headless=True, user_data_dir=None)
		browser_session = BrowserSession(browser_profile=browser_profile)
		event_bus = EventBus()
		watchdog = SecurityWatchdog(browser_session=browser_session, event_bus=event_bus)

		# Should match subdomains
		assert watchdog._is_url_allowed('https://sub.example.com') is True
		assert watchdog._is_url_allowed('https://deep.sub.example.com') is True

		# Should also match main domain
		assert watchdog._is_url_allowed('https://example.com') is True

		# Should not match other domains
		assert watchdog._is_url_allowed('https://notexample.com') is False
		assert watchdog._is_url_allowed('https://example.org') is False

		# Test more complex glob patterns
		browser_profile = BrowserProfile(
			allowed_domains=[
				'*.google.com',
				'https://wiki.org',
				'https://good.com',
				'https://*.test.com',
				'chrome://version',
				'brave://*',
			],
			headless=True,
			user_data_dir=None,
		)
		browser_session = BrowserSession(browser_profile=browser_profile)
		event_bus = EventBus()
		watchdog = SecurityWatchdog(browser_session=browser_session, event_bus=event_bus)

		# Should match domains ending with google.com
		assert watchdog._is_url_allowed('https://google.com') is True
		assert watchdog._is_url_allowed('https://www.google.com') is True
		assert (
			watchdog._is_url_allowed('https://evilgood.com') is False
		)  # make sure we dont allow *good.com patterns, only *.good.com

		# Should match domains starting with wiki
		assert watchdog._is_url_allowed('http://wiki.org') is False
		assert watchdog._is_url_allowed('https://wiki.org') is True

		# Should not match internal domains because scheme was not provided
		assert watchdog._is_url_allowed('chrome://google.com') is False
		assert watchdog._is_url_allowed('chrome://abc.google.com') is False

		# Test browser internal URLs
		assert watchdog._is_url_allowed('chrome://settings') is False
		assert watchdog._is_url_allowed('chrome://version') is True
		assert watchdog._is_url_allowed('chrome-extension://version/') is False
		assert watchdog._is_url_allowed('brave://anything/') is True
		assert watchdog._is_url_allowed('about:blank') is True
		assert watchdog._is_url_allowed('chrome://new-tab-page/') is True
		assert watchdog._is_url_allowed('chrome://new-tab-page') is True

		# Test security for glob patterns (authentication credentials bypass attempts)
		# These should all be detected as malicious despite containing allowed domain patterns
		assert watchdog._is_url_allowed('https://allowed.example.com:password@notallowed.com') is False
		assert watchdog._is_url_allowed('https://subdomain.example.com@evil.com') is False
		assert watchdog._is_url_allowed('https://sub.example.com%20@malicious.org') is False
		assert watchdog._is_url_allowed('https://anygoogle.com@evil.org') is False

		# Test pattern matching
		assert watchdog._is_url_allowed('https://www.test.com') is True
		assert watchdog._is_url_allowed('https://www.testx.com') is False