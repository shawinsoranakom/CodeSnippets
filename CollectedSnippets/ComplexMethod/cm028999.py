def test_invalid_ip_detection(self):
		"""Test that non-IP strings are correctly identified as not IPs."""
		browser_profile = BrowserProfile(block_ip_addresses=True, headless=True, user_data_dir=None)
		browser_session = BrowserSession(browser_profile=browser_profile)
		event_bus = EventBus()
		watchdog = SecurityWatchdog(browser_session=browser_session, event_bus=event_bus)

		# Domain names (not IPs)
		assert watchdog._is_ip_address('example.com') is False
		assert watchdog._is_ip_address('www.google.com') is False
		assert watchdog._is_ip_address('localhost') is False

		# Invalid IPs
		assert watchdog._is_ip_address('999.999.999.999') is False
		assert watchdog._is_ip_address('1.2.3') is False
		assert watchdog._is_ip_address('1.2.3.4.5') is False
		assert watchdog._is_ip_address('not-an-ip') is False
		assert watchdog._is_ip_address('') is False

		# IPs with ports or paths (not valid for the helper - it only checks hostnames)
		assert watchdog._is_ip_address('192.168.1.1:8080') is False
		assert watchdog._is_ip_address('192.168.1.1/path') is False