async def test_user_data_dir_not_allowed_to_corrupt_default_profile(self):
		"""Test user_data_dir handling for different browser channels and version mismatches."""
		# Test 1: Chromium with default user_data_dir and default channel should work fine
		session = BrowserSession(
			browser_profile=BrowserProfile(
				headless=True,
				user_data_dir=CONFIG.BROWSER_USE_DEFAULT_USER_DATA_DIR,
				channel=BROWSERUSE_DEFAULT_CHANNEL,  # chromium
				keep_alive=False,
			),
		)

		try:
			await session.start()
			assert session._cdp_client_root is not None
			# Verify the user_data_dir wasn't changed
			assert session.browser_profile.user_data_dir == CONFIG.BROWSER_USE_DEFAULT_USER_DATA_DIR
		finally:
			await session.kill()

		# Test 2: Chrome with default user_data_dir should change dir AND copy to temp
		profile2 = BrowserProfile(
			headless=True,
			user_data_dir=CONFIG.BROWSER_USE_DEFAULT_USER_DATA_DIR,
			channel=BrowserChannel.CHROME,
			keep_alive=False,
		)

		# The validator should have changed the user_data_dir to avoid corruption
		# And then _copy_profile copies it to a temp directory (Chrome only)
		assert profile2.user_data_dir != CONFIG.BROWSER_USE_DEFAULT_USER_DATA_DIR
		assert 'browser-use-user-data-dir-' in str(profile2.user_data_dir)

		# Test 3: Edge with default user_data_dir should also change
		profile3 = BrowserProfile(
			headless=True,
			user_data_dir=CONFIG.BROWSER_USE_DEFAULT_USER_DATA_DIR,
			channel=BrowserChannel.MSEDGE,
			keep_alive=False,
		)

		assert profile3.user_data_dir != CONFIG.BROWSER_USE_DEFAULT_USER_DATA_DIR
		assert profile3.user_data_dir == CONFIG.BROWSER_USE_DEFAULT_USER_DATA_DIR.parent / 'default-msedge'
		assert 'browser-use-user-data-dir-' not in str(profile3.user_data_dir)