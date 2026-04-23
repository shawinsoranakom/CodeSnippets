def test_glob_pattern_edge_cases(self):
		"""Test edge cases for glob pattern matching to ensure proper behavior."""
		from bubus import EventBus

		from browser_use.browser.watchdogs.security_watchdog import SecurityWatchdog

		# Test with domains containing glob pattern in the middle
		browser_profile = BrowserProfile(allowed_domains=['*.google.com', 'https://wiki.org'], headless=True, user_data_dir=None)
		browser_session = BrowserSession(browser_profile=browser_profile)
		event_bus = EventBus()
		watchdog = SecurityWatchdog(browser_session=browser_session, event_bus=event_bus)

		# Verify that 'wiki*' pattern doesn't match domains that merely contain 'wiki' in the middle
		assert watchdog._is_url_allowed('https://notawiki.com') is False
		assert watchdog._is_url_allowed('https://havewikipages.org') is False
		assert watchdog._is_url_allowed('https://my-wiki-site.com') is False

		# Verify that '*google.com' doesn't match domains that have 'google' in the middle
		assert watchdog._is_url_allowed('https://mygoogle.company.com') is False

		# Create context with potentially risky glob pattern that demonstrates security concerns
		browser_profile = BrowserProfile(allowed_domains=['*.google.com', '*.google.co.uk'], headless=True, user_data_dir=None)
		browser_session = BrowserSession(browser_profile=browser_profile)
		event_bus = EventBus()
		watchdog = SecurityWatchdog(browser_session=browser_session, event_bus=event_bus)

		# Should match legitimate Google domains
		assert watchdog._is_url_allowed('https://www.google.com') is True
		assert watchdog._is_url_allowed('https://mail.google.co.uk') is True

		# Shouldn't match potentially malicious domains with a similar structure
		# This demonstrates why the previous pattern was risky and why it's now rejected
		assert watchdog._is_url_allowed('https://www.google.evil.com') is False