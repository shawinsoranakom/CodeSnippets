def test_block_ipv4_with_ports_and_paths(self):
		"""Test that IPv4 addresses with ports and paths are blocked."""
		browser_profile = BrowserProfile(block_ip_addresses=True, headless=True, user_data_dir=None)
		browser_session = BrowserSession(browser_profile=browser_profile)
		event_bus = EventBus()
		watchdog = SecurityWatchdog(browser_session=browser_session, event_bus=event_bus)

		# With various ports
		assert watchdog._is_url_allowed('http://8.8.8.8:80/') is False
		assert watchdog._is_url_allowed('https://8.8.8.8:443/') is False
		assert watchdog._is_url_allowed('http://192.168.1.1:8080/') is False
		assert watchdog._is_url_allowed('http://10.0.0.1:3000/api') is False

		# With paths and query strings
		assert watchdog._is_url_allowed('http://1.2.3.4/path/to/resource') is False
		assert watchdog._is_url_allowed('http://5.6.7.8/api?key=value') is False
		assert watchdog._is_url_allowed('https://9.10.11.12/path/to/file.html#anchor') is False