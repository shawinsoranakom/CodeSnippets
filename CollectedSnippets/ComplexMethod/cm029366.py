def _handle_sessions(args: argparse.Namespace) -> int:
	"""List active daemon sessions."""
	home_dir = _get_home_dir()
	sessions: list[dict] = []

	# Discover sessions from union of PID files + state files
	session_names: set[str] = set()
	for pid_file in home_dir.glob('*.pid'):
		if pid_file.stem:
			session_names.add(pid_file.stem)
	for state_file in home_dir.glob('*.state.json'):
		name = state_file.name.removesuffix('.state.json')
		if name:
			session_names.add(name)

	for name in sorted(session_names):
		probe = _probe_session(name)

		if not probe.pid_alive:
			# Don't delete if socket is still reachable — daemon alive despite stale PID
			if not probe.socket_reachable:
				_clean_session_files(name)
				continue

		# Terminal state + dead PID already handled above.
		# If phase is terminal but PID is alive, the daemon restarted and
		# the stale state file belongs to a previous instance — only clean
		# the state file, not the PID/socket which the live daemon owns.
		if probe.phase in ('stopped', 'failed'):
			_get_state_path(name).unlink(missing_ok=True)
			# Fall through to show the live session

		entry: dict = {'name': name, 'pid': probe.pid or 0, 'phase': probe.phase or '?'}

		# Try to ping for config info
		if probe.socket_reachable:
			try:
				resp = send_command('ping', {}, session=name)
				if resp.get('success'):
					data = resp.get('data', {})
					config_parts = []
					if data.get('headed'):
						config_parts.append('headed')
					if data.get('profile'):
						config_parts.append(f'profile={data["profile"]}')
					if data.get('cdp_url'):
						entry['cdp_url'] = data['cdp_url']
						if not data.get('use_cloud'):
							config_parts.append('cdp')
					if data.get('use_cloud'):
						config_parts.append('cloud')
					entry['config'] = ', '.join(config_parts) if config_parts else 'headless'
			except Exception:
				entry['config'] = '?'
		else:
			entry['config'] = '?'

		sessions.append(entry)

	# Sweep orphaned sockets that have no corresponding live session
	live_names = {s['name'] for s in sessions}
	for sock_file in home_dir.glob('*.sock'):
		if sock_file.stem not in live_names:
			sock_file.unlink(missing_ok=True)

	if args.json:
		print(json.dumps({'sessions': sessions}))
	else:
		if sessions:
			print(f'{"SESSION":<16} {"PHASE":<14} {"PID":<8} CONFIG')
			for s in sessions:
				print(f'{s["name"]:<16} {s.get("phase", "?"):<14} {s["pid"]:<8} {s.get("config", "")}')
		else:
			print('No active sessions')

	return 0