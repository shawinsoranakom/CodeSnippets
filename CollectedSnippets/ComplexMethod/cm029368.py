def _handle_close_all(args: argparse.Namespace) -> int:
	"""Close all active sessions."""
	home_dir = _get_home_dir()

	# Discover sessions from union of PID files + state files
	session_names: set[str] = set()
	for pid_file in home_dir.glob('*.pid'):
		if pid_file.stem:
			session_names.add(pid_file.stem)
	for state_file in home_dir.glob('*.state.json'):
		name = state_file.name.removesuffix('.state.json')
		if name:
			session_names.add(name)

	closed = 0
	for name in sorted(session_names):
		if _close_session(name):
			closed += 1

	if args.json:
		print(json.dumps({'closed': closed}))
	else:
		if closed:
			print(f'Closed {closed} session(s)')
		else:
			print('No active sessions')

	return 0