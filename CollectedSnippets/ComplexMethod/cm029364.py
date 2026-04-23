def ensure_daemon(
	headed: bool,
	profile: str | None,
	cdp_url: str | None = None,
	*,
	session: str = 'default',
	explicit_config: bool = False,
	use_cloud: bool = False,
	cloud_profile_id: str | None = None,
	cloud_proxy_country_code: str | None = None,
	cloud_timeout: int | None = None,
) -> None:
	"""Start daemon if not running. Uses state file for phase-aware decisions."""
	probe = _probe_session(session)

	# Socket reachable — daemon is alive and responding
	if probe.socket_reachable:
		if not explicit_config:
			return  # Reuse it

		# User explicitly set --headed/--profile/--cdp-url — check config matches
		try:
			response = send_command('ping', {}, session=session)
			if response.get('success'):
				data = response.get('data', {})
				if (
					data.get('headed') == headed
					and data.get('profile') == profile
					and data.get('cdp_url') == cdp_url
					and data.get('use_cloud') == use_cloud
				):
					return  # Already running with correct config

				# Config mismatch — error, don't auto-restart (avoids orphan cascades)
				print(
					f'Error: Session {session!r} is already running with different config.\n'
					f'Run `browser-use{" --session " + session if session != "default" else ""} close` first.',
					file=sys.stderr,
				)
				sys.exit(1)
			return  # Ping returned failure — daemon alive but can't verify config, reuse it
		except Exception:
			return  # Daemon alive but not responsive — reuse it, can't safely restart

	# Socket unreachable but process alive — phase-aware decisions
	if probe.pid_alive and probe.phase:
		now = time.time()
		age = now - probe.updated_at if probe.updated_at else float('inf')

		if probe.phase == 'initializing' and age < 15:
			# Daemon is booting, wait for socket
			for _ in range(30):
				time.sleep(0.5)
				if _is_daemon_alive(session):
					return
			# Still not reachable — fall through to error

		elif probe.phase in ('starting', 'ready', 'running') and age < 60:
			# Daemon is alive but socket broke, or starting browser
			print(
				f'Error: Session {session!r} is alive (phase={probe.phase}) but socket unreachable.\n'
				f'Run `browser-use{" --session " + session if session != "default" else ""} close` first.',
				file=sys.stderr,
			)
			sys.exit(1)

		elif probe.phase == 'shutting_down' and age < 15:
			# Daemon is shutting down, wait for it to finish
			for _ in range(30):
				time.sleep(0.5)
				if not probe.pid or not _is_pid_alive(probe.pid):
					break
			# Fall through to spawn

		# Stale phase — daemon stuck or crashed without terminal state
		elif probe.pid and _is_daemon_process(probe.pid):
			_terminate_pid(probe.pid)

	# Clean up stale files before spawning
	_clean_session_files(session)

	# Build daemon command
	cmd = [
		sys.executable,
		'-m',
		'browser_use.skill_cli.daemon',
		'--session',
		session,
	]
	if headed:
		cmd.append('--headed')
	if profile:
		cmd.extend(['--profile', profile])
	if cdp_url:
		cmd.extend(['--cdp-url', cdp_url])
	if use_cloud:
		cmd.append('--use-cloud')
	if cloud_profile_id is not None:
		cmd.extend(['--cloud-profile-id', cloud_profile_id])
	if cloud_proxy_country_code is not None:
		cmd.extend(['--cloud-proxy-country', cloud_proxy_country_code])
	if cloud_timeout is not None:
		cmd.extend(['--cloud-timeout', str(cloud_timeout)])

	# Set up environment
	env = os.environ.copy()

	# For cloud mode, inject API key from config.json into daemon env.
	# The library's CloudBrowserClient reads BROWSER_USE_API_KEY env var directly,
	# so we inject it to prevent fallback to ~/.config/browseruse/cloud_auth.json.
	if use_cloud:
		from browser_use.skill_cli.config import get_config_value

		cli_api_key = get_config_value('api_key')
		if cli_api_key:
			env['BROWSER_USE_API_KEY'] = str(cli_api_key)

	# Start daemon as background process
	if sys.platform == 'win32':
		subprocess.Popen(
			cmd,
			env=env,
			creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
		)
	else:
		subprocess.Popen(
			cmd,
			env=env,
			start_new_session=True,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
		)

	# Wait for daemon to be ready — use state file for phase-aware waiting
	deadline = time.time() + 15
	while time.time() < deadline:
		probe = _probe_session(session)
		if probe.socket_reachable:
			return
		# Daemon wrote state and PID is alive — still booting, keep waiting
		if probe.pid_alive and probe.phase in ('initializing', 'ready', 'starting', 'running'):
			time.sleep(0.2)
			continue
		# Daemon wrote terminal state — startup failed
		if probe.phase in ('failed', 'stopped'):
			break
		time.sleep(0.2)

	print('Error: Failed to start daemon', file=sys.stderr)
	sys.exit(1)