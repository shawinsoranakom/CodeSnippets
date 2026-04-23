def handle_cloud_command(argv: list[str]) -> int:
	"""Main dispatcher for `browser-use cloud ...`."""
	if not argv:
		_print_cloud_usage()
		return 1

	subcmd = argv[0]

	if subcmd == 'login':
		return _cloud_login(argv[1:])

	if subcmd == 'logout':
		return _cloud_logout()

	if subcmd in ('v2', 'v3'):
		return _cloud_versioned(argv[1:], subcmd)

	if subcmd == 'signup':
		if '--verify' in argv:
			idx = argv.index('--verify')
			if idx + 2 >= len(argv):
				print('Usage: browser-use cloud signup --verify <challenge-id> <answer>', file=sys.stderr)
				return 1
			return _signup_verify(argv[idx + 1], argv[idx + 2])
		if '--claim' in argv:
			return _signup_claim()
		return _signup_challenge()

	if subcmd == 'connect':
		# Normally intercepted by main.py before reaching here
		print('Error: cloud connect must be run via the main CLI (browser-use cloud connect)', file=sys.stderr)
		return 1

	if subcmd in ('--help', 'help', '-h'):
		_print_cloud_usage()
		return 0

	print(f'Unknown cloud subcommand: {subcmd}', file=sys.stderr)
	_print_cloud_usage()
	return 1