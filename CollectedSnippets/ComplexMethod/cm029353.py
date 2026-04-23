def get_chrome_user_data_dirs() -> list[Path]:
	"""Return candidate Chrome/Chromium user-data directories for the current OS.

	Covers Google Chrome, Chrome Canary, Chromium, and Brave on macOS/Linux/Windows.
	"""
	system = platform.system()
	home = Path.home()
	candidates: list[Path] = []

	if system == 'Darwin':
		base = home / 'Library' / 'Application Support'
		for name in ('Google/Chrome', 'Google/Chrome Canary', 'Chromium', 'BraveSoftware/Brave-Browser'):
			candidates.append(base / name)
	elif system == 'Linux':
		base = home / '.config'
		for name in ('google-chrome', 'google-chrome-unstable', 'chromium', 'BraveSoftware/Brave-Browser'):
			candidates.append(base / name)
	elif system == 'Windows':
		local_app_data = os.environ.get('LOCALAPPDATA', str(home / 'AppData' / 'Local'))
		base = Path(local_app_data)
		for name in (
			'Google\\Chrome\\User Data',
			'Google\\Chrome SxS\\User Data',
			'Chromium\\User Data',
			'BraveSoftware\\Brave-Browser\\User Data',
		):
			candidates.append(base / name)

	return [d for d in candidates if d.is_dir()]