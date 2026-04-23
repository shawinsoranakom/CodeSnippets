def _close_session(session: str) -> bool:
	"""Close a single session. Returns True if something was closed/killed.

	Only cleans up files after the daemon process is confirmed dead.
	"""
	probe = _probe_session(session)

	if probe.socket_reachable:
		print('Closing...', end='', flush=True)
		try:
			send_command('shutdown', {}, session=session)
		except Exception:
			pass  # Shutdown may have been accepted even if response failed
		# Poll for PID disappearance (up to 15s: 10s browser cleanup + margin)
		confirmed_dead = not probe.pid  # No PID to check = assume success
		if probe.pid:
			for _ in range(150):
				time.sleep(0.1)
				if not _is_pid_alive(probe.pid):
					confirmed_dead = True
					break
		if confirmed_dead:
			_clean_session_files(session)
		return True

	if probe.pid_alive and probe.pid and _is_daemon_process(probe.pid):
		dead = _terminate_pid(probe.pid)
		if dead:
			_clean_session_files(session)
		return dead

	# Nothing alive — clean up stale files if any exist
	if probe.pid or probe.phase:
		_clean_session_files(session)
	return False