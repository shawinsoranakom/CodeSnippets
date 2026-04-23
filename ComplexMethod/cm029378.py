def handle(yes: bool = False) -> dict:
	"""Run interactive setup."""
	from browser_use.skill_cli.utils import get_home_dir

	home_dir = get_home_dir()
	results: dict = {}
	step = 0
	total = 6

	print('\nBrowser-Use Setup')
	print('━━━━━━━━━━━━━━━━━\n')

	# Step 1: Home directory
	step += 1
	print(f'Step {step}/{total}: Home directory')
	if home_dir.exists():
		print(f'  ✓ {home_dir} exists')
	else:
		home_dir.mkdir(parents=True, exist_ok=True)
		print(f'  ✓ {home_dir} created')
	results['home_dir'] = 'ok'

	# Step 2: Config file
	step += 1
	config_path = home_dir / 'config.json'
	print(f'\nStep {step}/{total}: Config file')
	if config_path.exists():
		print(f'  ✓ {config_path} exists')
	else:
		config_path.write_text('{}\n')
		try:
			config_path.chmod(0o600)
		except OSError:
			pass
		print(f'  ✓ {config_path} created')
	results['config'] = 'ok'

	# Step 3: Chromium browser
	step += 1
	print(f'\nStep {step}/{total}: Chromium browser')
	chromium_installed = _check_chromium()
	if chromium_installed:
		print('  ✓ Chromium already installed')
		results['chromium'] = 'ok'
	else:
		if _prompt('Chromium is not installed (~300MB download). Install now?', yes):
			print('  ℹ Installing Chromium...')
			if _install_chromium():
				print('  ✓ Chromium installed')
				results['chromium'] = 'ok'
			else:
				print('  ✗ Chromium installation failed')
				results['chromium'] = 'failed'
		else:
			print('  ○ Skipped')
			results['chromium'] = 'skipped'

	# Step 4: Profile-use binary
	step += 1
	print(f'\nStep {step}/{total}: Profile-use binary')
	from browser_use.skill_cli.profile_use import get_profile_use_binary

	if get_profile_use_binary():
		print('  ✓ profile-use already installed')
		results['profile_use'] = 'ok'
	else:
		if _prompt('profile-use is not installed (needed for browser-use profile). Install now?', yes):
			print('  ℹ Downloading profile-use...')
			if _install_profile_use():
				print('  ✓ profile-use installed')
				results['profile_use'] = 'ok'
			else:
				print('  ✗ profile-use installation failed')
				results['profile_use'] = 'failed'
		else:
			print('  ○ Skipped')
			results['profile_use'] = 'skipped'

	# Step 5: Cloudflared
	step += 1
	print(f'\nStep {step}/{total}: Cloudflare tunnel (cloudflared)')
	if shutil.which('cloudflared'):
		print('  ✓ cloudflared already installed')
		results['cloudflared'] = 'ok'
	else:
		if _prompt('cloudflared is not installed (needed for browser-use tunnel). Install now?', yes):
			print('  ℹ Installing cloudflared...')
			if _install_cloudflared():
				print('  ✓ cloudflared installed')
				results['cloudflared'] = 'ok'
			else:
				print('  ✗ cloudflared installation failed')
				results['cloudflared'] = 'failed'
		else:
			print('  ○ Skipped')
			results['cloudflared'] = 'skipped'

	# Step 6: Validation
	step += 1
	print(f'\nStep {step}/{total}: Validation')
	from browser_use.skill_cli.config import CLI_DOCS_URL, get_config_display

	# Quick checks
	checks = {
		'package': _check_package(),
		'browser': 'ok' if _check_chromium() else 'missing',
		'profile_use': 'ok' if get_profile_use_binary() else 'missing',
		'cloudflared': 'ok' if shutil.which('cloudflared') else 'missing',
	}
	for name, status in checks.items():
		icon = '✓' if status == 'ok' else '○'
		print(f'  {icon} {name}: {status}')

	# Config display
	entries = get_config_display()
	print(f'\nConfig ({config_path}):')
	for entry in entries:
		if entry['is_set']:
			icon = '✓'
			val = 'set' if entry['sensitive'] else entry['value']
		else:
			icon = '○'
			val = entry['value'] if entry['value'] else 'not set'
		print(f'  {icon} {entry["key"]}: {val}')
	print(f'  Docs: {CLI_DOCS_URL}')

	print('\n━━━━━━━━━━━━━━━━━')
	print('Setup complete! Next: browser-use open https://example.com\n')

	results['status'] = 'success'
	return results