def _handle_cloud_connect(cloud_args: list[str], args: argparse.Namespace, session: str) -> int:
	"""Handle `browser-use cloud connect` — zero-config cloud browser provisioning."""
	# Mutual exclusivity checks
	if getattr(args, 'connect', False):
		print('Error: --connect and cloud connect are mutually exclusive', file=sys.stderr)
		return 1
	if args.cdp_url:
		print('Error: --cdp-url and cloud connect are mutually exclusive', file=sys.stderr)
		return 1
	if args.profile:
		print('Error: --profile and cloud connect are mutually exclusive', file=sys.stderr)
		return 1

	# Validate API key exists before spawning daemon (shows our CLI error, not library's)
	from browser_use.skill_cli.commands.cloud import (
		_get_api_key,
		_get_cloud_connect_proxy,
		_get_cloud_connect_timeout,
		_get_or_create_cloud_profile,
	)

	_get_api_key()  # exits with helpful message if no key

	cloud_profile_id = _get_or_create_cloud_profile()

	# Start daemon with cloud config
	if not args.json:
		print('Connecting...', end='', flush=True)
	ensure_daemon(
		args.headed,
		None,
		session=session,
		explicit_config=True,
		use_cloud=True,
		cloud_profile_id=cloud_profile_id,
		cloud_proxy_country_code=_get_cloud_connect_proxy(),
		cloud_timeout=_get_cloud_connect_timeout(),
	)

	# Send connect command to force immediate session creation
	response = send_command('connect', {}, session=session)

	if args.json:
		print(json.dumps(response))
	else:
		print('\r' + ' ' * 20 + '\r', end='')  # clear "Connecting..."
		if response.get('success'):
			data = response.get('data', {})
			print(f'status: {data.get("status", "unknown")}')
			if 'live_url' in data:
				print(f'live_url: {data["live_url"]}')
			if 'cdp_url' in data:
				print(f'cdp_url: {data["cdp_url"]}')
		else:
			print(f'Error: {response.get("error")}', file=sys.stderr)
			return 1

	return 0