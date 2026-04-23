async def test_cdp_client_headers_passed_on_connect():
	"""Test that headers from BrowserProfile are passed to CDPClient on connect()."""
	test_headers = {
		'Authorization': 'AWS4-HMAC-SHA256 Credential=test...',
		'X-Amz-Date': '20250914T163733Z',
		'X-Amz-Security-Token': 'test-token',
		'Host': 'remote-browser.example.com',
	}

	session = BrowserSession(cdp_url='wss://remote-browser.example.com/cdp', headers=test_headers)

	with patch('browser_use.browser.session.TimeoutWrappedCDPClient') as mock_cdp_client_class:
		# Setup mock CDPClient instance
		mock_cdp_client = AsyncMock()
		mock_cdp_client_class.return_value = mock_cdp_client
		mock_cdp_client.start = AsyncMock()
		mock_cdp_client.stop = AsyncMock()

		# Mock CDP methods
		mock_cdp_client.send = MagicMock()
		mock_cdp_client.send.Target = MagicMock()
		mock_cdp_client.send.Target.setAutoAttach = AsyncMock()
		mock_cdp_client.send.Target.getTargets = AsyncMock(return_value={'targetInfos': []})
		mock_cdp_client.send.Target.createTarget = AsyncMock(return_value={'targetId': 'test-target-id'})

		# Mock SessionManager (imported inside connect() from browser_use.browser.session_manager)
		with patch('browser_use.browser.session_manager.SessionManager') as mock_session_manager_class:
			mock_session_manager = MagicMock()
			mock_session_manager_class.return_value = mock_session_manager
			mock_session_manager.start_monitoring = AsyncMock()
			mock_session_manager.get_all_page_targets = MagicMock(return_value=[])

			try:
				await session.connect()
			except Exception:
				# May fail due to incomplete mocking, but we can still verify the key assertion
				pass

			# Verify CDPClient was instantiated with the headers
			mock_cdp_client_class.assert_called_once()
			call_kwargs = mock_cdp_client_class.call_args

			# Check positional args and keyword args
			assert call_kwargs[0][0] == 'wss://remote-browser.example.com/cdp', 'CDP URL should be first arg'
			actual_headers = call_kwargs[1].get('additional_headers')
			# All user-provided headers must be present
			for key, value in test_headers.items():
				assert actual_headers[key] == value, f'Header {key} should be passed as additional_headers'
			# User-Agent should be injected for remote connections
			assert 'User-Agent' in actual_headers, 'User-Agent should be injected for remote connections'
			assert actual_headers['User-Agent'].startswith('browser-use/'), 'User-Agent should start with browser-use/'
			assert call_kwargs[1].get('max_ws_frame_size') == 200 * 1024 * 1024, 'max_ws_frame_size should be set'