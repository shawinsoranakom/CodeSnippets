def _find_installed_browser_path(channel: BrowserChannel | None = None) -> str | None:
		"""Try to find browser executable from common fallback locations.

		If a channel is specified, paths for that browser are searched first.
		Falls back to all known browser paths if the channel-specific search fails.

		Prioritizes:
		1. Channel-specific paths (if channel is set to a non-default value)
		2. Playwright bundled Chromium (when no channel or default channel specified)
		3. System Chrome stable
		4. Other system native browsers (Chromium -> Chrome Canary/Dev -> Brave -> Edge)
		5. Playwright headless-shell fallback

		Returns:
			Path to browser executable or None if not found
		"""
		import glob
		import platform
		from pathlib import Path

		from browser_use.browser.profile import BROWSERUSE_DEFAULT_CHANNEL, BrowserChannel

		system = platform.system()

		# Get playwright browsers path from environment variable if set
		playwright_path = os.environ.get('PLAYWRIGHT_BROWSERS_PATH')

		# Build tagged pattern lists per OS: (browser_group, path)
		# browser_group is used to match against the requested channel
		if system == 'Darwin':  # macOS
			if not playwright_path:
				playwright_path = '~/Library/Caches/ms-playwright'
			all_patterns = [
				('chrome', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
				('chromium', f'{playwright_path}/chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium'),
				('chromium', '/Applications/Chromium.app/Contents/MacOS/Chromium'),
				('chrome-canary', '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'),
				('brave', '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'),
				('msedge', '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),
				('chromium', f'{playwright_path}/chromium_headless_shell-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium'),
			]
		elif system == 'Linux':
			if not playwright_path:
				playwright_path = '~/.cache/ms-playwright'
			all_patterns = [
				('chrome', '/usr/bin/google-chrome-stable'),
				('chrome', '/usr/bin/google-chrome'),
				('chrome', '/usr/local/bin/google-chrome'),
				('chromium', f'{playwright_path}/chromium-*/chrome-linux*/chrome'),
				('chromium', '/usr/bin/chromium'),
				('chromium', '/usr/bin/chromium-browser'),
				('chromium', '/usr/local/bin/chromium'),
				('chromium', '/snap/bin/chromium'),
				('chrome-beta', '/usr/bin/google-chrome-beta'),
				('chrome-dev', '/usr/bin/google-chrome-dev'),
				('brave', '/usr/bin/brave-browser'),
				('msedge', '/usr/bin/microsoft-edge-stable'),
				('msedge', '/usr/bin/microsoft-edge'),
				('chromium', f'{playwright_path}/chromium_headless_shell-*/chrome-linux*/chrome'),
			]
		elif system == 'Windows':
			if not playwright_path:
				playwright_path = r'%LOCALAPPDATA%\ms-playwright'
			all_patterns = [
				('chrome', r'C:\Program Files\Google\Chrome\Application\chrome.exe'),
				('chrome', r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'),
				('chrome', r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe'),
				('chrome', r'%PROGRAMFILES%\Google\Chrome\Application\chrome.exe'),
				('chrome', r'%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe'),
				('chromium', f'{playwright_path}\\chromium-*\\chrome-win\\chrome.exe'),
				('chromium', r'C:\Program Files\Chromium\Application\chrome.exe'),
				('chromium', r'C:\Program Files (x86)\Chromium\Application\chrome.exe'),
				('chromium', r'%LOCALAPPDATA%\Chromium\Application\chrome.exe'),
				('brave', r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe'),
				('brave', r'C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe'),
				('msedge', r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'),
				('msedge', r'C:\Program Files\Microsoft\Edge\Application\msedge.exe'),
				('msedge', r'%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe'),
				('chromium', f'{playwright_path}\\chromium_headless_shell-*\\chrome-win\\chrome.exe'),
			]
		else:
			all_patterns = []

		# Map channel enum values to browser group tags
		_channel_to_group: dict[BrowserChannel, str] = {
			BrowserChannel.CHROME: 'chrome',
			BrowserChannel.CHROME_BETA: 'chrome-beta',
			BrowserChannel.CHROME_DEV: 'chrome-dev',
			BrowserChannel.CHROME_CANARY: 'chrome-canary',
			BrowserChannel.CHROMIUM: 'chromium',
			BrowserChannel.MSEDGE: 'msedge',
			BrowserChannel.MSEDGE_BETA: 'msedge',
			BrowserChannel.MSEDGE_DEV: 'msedge',
			BrowserChannel.MSEDGE_CANARY: 'msedge',
		}

		# Prioritize the target browser group, then fall back to the rest.
		if channel and channel != BROWSERUSE_DEFAULT_CHANNEL and channel in _channel_to_group:
			target_group = _channel_to_group[channel]
		else:
			target_group = _channel_to_group[BROWSERUSE_DEFAULT_CHANNEL]
		prioritized = [p for g, p in all_patterns if g == target_group]
		rest = [p for g, p in all_patterns if g != target_group]
		patterns = prioritized + rest

		for pattern in patterns:
			# Expand user home directory
			expanded_pattern = Path(pattern).expanduser()

			# Handle Windows environment variables
			if system == 'Windows':
				pattern_str = str(expanded_pattern)
				for env_var in ['%LOCALAPPDATA%', '%PROGRAMFILES%', '%PROGRAMFILES(X86)%']:
					if env_var in pattern_str:
						env_key = env_var.strip('%').replace('(X86)', ' (x86)')
						env_value = os.environ.get(env_key, '')
						if env_value:
							pattern_str = pattern_str.replace(env_var, env_value)
				expanded_pattern = Path(pattern_str)

			# Convert to string for glob
			pattern_str = str(expanded_pattern)

			# Check if pattern contains wildcards
			if '*' in pattern_str:
				# Use glob to expand the pattern
				matches = glob.glob(pattern_str)
				if matches:
					# Sort matches and take the last one (alphanumerically highest version)
					matches.sort()
					browser_path = matches[-1]
					if Path(browser_path).exists() and Path(browser_path).is_file():
						return browser_path
			else:
				# Direct path check
				if expanded_pattern.exists() and expanded_pattern.is_file():
					return str(expanded_pattern)

		return None