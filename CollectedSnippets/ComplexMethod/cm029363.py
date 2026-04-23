def _probe_session(session: str) -> _SessionProbe:
	"""Non-destructive probe of a session's state. Never deletes files."""
	probe = _SessionProbe(name=session)

	# 1. Read state file
	state = _read_session_state(session)
	state_pid: int | None = None
	if state:
		probe.phase = state.get('phase')
		probe.updated_at = state.get('updated_at')
		state_pid = state.get('pid')

	# 2. Read PID file
	pid_file_pid: int | None = None
	pid_path = _get_pid_path(session)
	if pid_path.exists():
		try:
			pid_file_pid = int(pid_path.read_text().strip())
		except (OSError, ValueError):
			pass

	# 3. Try socket connect + ping for PID (before reconciliation)
	try:
		sock = _connect_to_daemon(timeout=0.5, session=session)
		sock.close()
		probe.socket_reachable = True
		try:
			resp = send_command('ping', {}, session=session)
			if resp.get('success'):
				probe.socket_pid = resp.get('data', {}).get('pid')
		except Exception:
			pass
	except OSError:
		probe.socket_reachable = False

	# 4. Reconcile PIDs
	state_alive = bool(state_pid and _is_pid_alive(state_pid))
	pidfile_alive = bool(pid_file_pid and _is_pid_alive(pid_file_pid))

	if state_alive and pidfile_alive and state_pid != pid_file_pid:
		# Split-brain: both PIDs alive but different.
		# Use socket_pid to break the tie.
		if probe.socket_pid == state_pid:
			probe.pid = state_pid
		elif probe.socket_pid == pid_file_pid:
			probe.pid = pid_file_pid
		else:
			# Socket unreachable or answers with unknown PID — can't resolve
			probe.pid = pid_file_pid  # .pid file is written later, so prefer it
		probe.pid_alive = True
	elif state_alive:
		probe.pid = state_pid
		probe.pid_alive = True
	elif pidfile_alive:
		probe.pid = pid_file_pid
		probe.pid_alive = True
	else:
		probe.pid = state_pid or pid_file_pid
		probe.pid_alive = False

	return probe