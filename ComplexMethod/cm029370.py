def main() -> int:
	"""Main entry point."""
	parser = build_parser()
	args = parser.parse_args()

	if not args.command:
		parser.print_help()
		return 0

	# Resolve session name
	session = args.session or os.environ.get('BROWSER_USE_SESSION', 'default')
	if not re.match(r'^[a-zA-Z0-9_-]+$', session):
		print(f'Error: Invalid session name {session!r}: only letters, digits, hyphens, underscores', file=sys.stderr)
		return 1

	# Handle sessions command (before daemon interaction)
	if args.command == 'sessions':
		return _handle_sessions(args)

	# Handle cloud subcommands
	if args.command == 'cloud':
		cloud_args = getattr(args, 'cloud_args', [])

		# Intercept 'cloud connect' — needs daemon, not REST passthrough
		if cloud_args and cloud_args[0] == 'connect':
			return _handle_cloud_connect(cloud_args[1:], args, session)

		# All other cloud subcommands are stateless REST passthroughs
		from browser_use.skill_cli.commands.cloud import handle_cloud_command

		return handle_cloud_command(cloud_args)

	# Handle profile subcommand — passthrough to profile-use Go binary
	if args.command == 'profile':
		from browser_use.skill_cli.profile_use import run_profile_use

		profile_argv = getattr(args, 'profile_args', [])
		return run_profile_use(profile_argv)

	# Handle setup command
	if args.command == 'setup':
		from browser_use.skill_cli.commands import setup

		result = setup.handle(yes=getattr(args, 'yes', False))

		if args.json:
			print(json.dumps(result))
		elif 'error' in result:
			print(f'Error: {result["error"]}', file=sys.stderr)
			return 1
		return 0

	# Handle doctor command
	if args.command == 'doctor':
		from browser_use.skill_cli.commands import doctor

		result = asyncio.run(doctor.handle())

		if args.json:
			print(json.dumps(result))
		else:
			# Print check results
			checks = result.get('checks', {})
			print('\nDiagnostics:\n')
			for name, check in checks.items():
				status = check.get('status', 'unknown')
				message = check.get('message', '')
				note = check.get('note', '')
				fix = check.get('fix', '')

				if status == 'ok':
					icon = '✓'
				elif status == 'warning':
					icon = '⚠'
				elif status == 'missing':
					icon = '○'
				else:
					icon = '✗'

				print(f'  {icon} {name}: {message}')
				if note:
					print(f'      {note}')
				if fix:
					print(f'      Fix: {fix}')

			print('')
			if result.get('status') == 'healthy':
				print('✓ All checks passed!')
			else:
				print(f'⚠ {result.get("summary", "Some checks need attention")}')

			# Show config state
			from browser_use.skill_cli.config import CLI_DOCS_URL, get_config_display

			entries = get_config_display()
			print(f'\nConfig ({_get_home_dir() / "config.json"}):\n')
			for entry in entries:
				if entry['is_set']:
					icon = '✓'
					val = 'set' if entry['sensitive'] else entry['value']
				else:
					icon = '○'
					val = entry['value'] if entry['value'] else 'not set'
				print(f'  {icon} {entry["key"]}: {val}')
			print(f'  Docs: {CLI_DOCS_URL}')

		return 0

	# Handle config command
	if args.command == 'config':
		from browser_use.skill_cli.config import (
			CLI_DOCS_URL,
			get_config_display,
			get_config_value,
			set_config_value,
			unset_config_value,
		)

		config_cmd = getattr(args, 'config_command', None)

		if config_cmd == 'set':
			try:
				set_config_value(args.key, args.value)
				print(f'{args.key} = {args.value}')
			except ValueError as e:
				print(f'Error: {e}', file=sys.stderr)
				return 1

		elif config_cmd == 'get':
			val = get_config_value(args.key)
			if val is not None:
				print(val)
			else:
				print(f'{args.key}: not set', file=sys.stderr)

		elif config_cmd == 'unset':
			try:
				unset_config_value(args.key)
				print(f'{args.key} removed')
			except ValueError as e:
				print(f'Error: {e}', file=sys.stderr)
				return 1

		elif config_cmd == 'list' or config_cmd is None:
			entries = get_config_display()
			print(f'Config ({_get_home_dir() / "config.json"}):')
			for entry in entries:
				if entry['is_set']:
					icon = '✓'
					val = 'set' if entry['sensitive'] else entry['value']
				else:
					icon = '○'
					val = entry['value'] if entry['value'] else 'not set'
				print(f'  {icon} {entry["key"]}: {val}')
			print(f'  Docs: {CLI_DOCS_URL}')

		return 0

	# Handle tunnel command - runs independently of browser session
	if args.command == 'tunnel':
		from browser_use.skill_cli import tunnel

		pos = getattr(args, 'port_or_subcommand', None)

		if pos == 'list':
			result = tunnel.list_tunnels()
		elif pos == 'stop':
			port_arg = getattr(args, 'port_arg', None)
			if getattr(args, 'all', False):
				# stop --all
				result = asyncio.run(tunnel.stop_all_tunnels())
			elif port_arg is not None:
				result = asyncio.run(tunnel.stop_tunnel(port_arg))
			else:
				print('Usage: browser-use tunnel stop <port> | --all', file=sys.stderr)
				return 1
		elif pos is not None:
			try:
				port = int(pos)
			except ValueError:
				print(f'Unknown tunnel subcommand: {pos}', file=sys.stderr)
				return 1
			result = asyncio.run(tunnel.start_tunnel(port))
		else:
			print('Usage: browser-use tunnel <port> | list | stop <port>', file=sys.stderr)
			return 0

		# Output result
		if args.json:
			print(json.dumps(result))
		else:
			if 'error' in result:
				print(f'Error: {result["error"]}', file=sys.stderr)
				return 1
			elif 'url' in result:
				existing = ' (existing)' if result.get('existing') else ''
				print(f'url: {result["url"]}{existing}')
			elif 'tunnels' in result:
				if result['tunnels']:
					for t in result['tunnels']:
						print(f'  port {t["port"]}: {t["url"]}')
				else:
					print('No active tunnels')
			elif 'stopped' in result:
				if isinstance(result['stopped'], list):
					if result['stopped']:
						print(f'Stopped {len(result["stopped"])} tunnel(s): {", ".join(map(str, result["stopped"]))}')
					else:
						print('No tunnels to stop')
				else:
					print(f'Stopped tunnel on port {result["stopped"]}')
		return 0

	# Handle close — shutdown daemon
	if args.command == 'close':
		if getattr(args, 'all', False):
			return _handle_close_all(args)

		closed = _close_session(session)
		if args.json:
			print(json.dumps({'success': True, 'data': {'shutdown': True}}))
		else:
			print('\r' + ' ' * 20 + '\r', end='')  # clear "Closing..."
			if closed:
				print('Browser closed')
			elif closed is False and _probe_session(session).pid_alive:
				print('Warning: daemon may still be shutting down', file=sys.stderr)
			else:
				print('No active browser session')
		return 0

	# Handle --connect deprecation
	if args.connect:
		print('Note: --connect has been replaced.', file=sys.stderr)
		print('  To connect to Chrome:  browser-use connect', file=sys.stderr)
		print('  For cloud browser:     browser-use cloud connect', file=sys.stderr)
		print('  For multiple agents:   use --session NAME per agent', file=sys.stderr)
		return 1

	# Handle connect command (discover local Chrome, start daemon)
	if args.command == 'connect':
		from browser_use.skill_cli.utils import discover_chrome_cdp_url

		try:
			cdp_url = discover_chrome_cdp_url()
		except RuntimeError as e:
			print(f'Error: {e}', file=sys.stderr)
			return 1

		ensure_daemon(args.headed, None, cdp_url=cdp_url, session=session, explicit_config=True)
		response = send_command('connect', {}, session=session)

		if args.json:
			print(json.dumps(response))
		else:
			if response.get('success'):
				data = response.get('data', {})
				print(f'status: {data.get("status", "unknown")}')
				if 'cdp_url' in data:
					print(f'cdp_url: {data["cdp_url"]}')
			else:
				print(f'Error: {response.get("error")}', file=sys.stderr)
				return 1
		return 0

	# Mutual exclusivity
	if args.cdp_url and args.profile:
		print('Error: --cdp-url and --profile are mutually exclusive', file=sys.stderr)
		return 1

	# One-time legacy migration
	_migrate_legacy_files()

	# Ensure daemon is running
	explicit_config = any(flag in sys.argv for flag in ('--headed', '--profile', '--cdp-url'))
	ensure_daemon(args.headed, args.profile, args.cdp_url, session=session, explicit_config=explicit_config)

	# Build params from args
	params = {}
	skip_keys = {'command', 'headed', 'json', 'cdp_url', 'session', 'connect'}

	for key, value in vars(args).items():
		if key not in skip_keys and value is not None:
			params[key] = value

	# Resolve file paths to absolute before sending to daemon (daemon may have different CWD)
	if args.command == 'upload' and 'path' in params:
		params['path'] = str(Path(params['path']).expanduser().resolve())
	if args.command == 'record' and params.get('record_command') == 'start' and 'path' in params:
		params['path'] = str(Path(params['path']).expanduser().resolve())

	# Add profile to params for commands that need it
	if args.profile:
		params['profile'] = args.profile

	# Send command to daemon
	response = send_command(args.command, params, session=session)

	# Output response
	if args.json:
		print(json.dumps(response))
	else:
		if response.get('success'):
			data = response.get('data')
			if data is not None:
				if isinstance(data, dict):
					# Special case: raw text output (e.g., state command)
					if '_raw_text' in data:
						print(data['_raw_text'])
					else:
						for key, value in data.items():
							# Skip internal fields
							if key.startswith('_'):
								continue
							if key == 'screenshot' and len(str(value)) > 100:
								print(f'{key}: <{len(value)} bytes>')
							else:
								print(f'{key}: {value}')
				elif isinstance(data, str):
					print(data)
				else:
					print(data)
		else:
			print(f'Error: {response.get("error")}', file=sys.stderr)
			return 1

	return 0