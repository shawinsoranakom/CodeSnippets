def _migrate_legacy_files() -> None:
	"""One-time cleanup of old daemon files and config migration."""
	# Migrate config from old XDG location
	from browser_use.skill_cli.utils import migrate_legacy_paths

	migrate_legacy_paths()

	# Clean up old single-socket daemon (pre-multi-session)
	legacy_path = Path(tempfile.gettempdir()) / 'browser-use-cli.sock'
	if sys.platform == 'win32':
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			sock.settimeout(0.5)
			sock.connect(('127.0.0.1', 49200))
			req = json.dumps({'id': 'legacy', 'action': 'shutdown', 'params': {}}) + '\n'
			sock.sendall(req.encode())
		except OSError:
			pass
		finally:
			sock.close()
	elif legacy_path.exists():
		sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		try:
			sock.settimeout(0.5)
			sock.connect(str(legacy_path))
			req = json.dumps({'id': 'legacy', 'action': 'shutdown', 'params': {}}) + '\n'
			sock.sendall(req.encode())
		except OSError:
			legacy_path.unlink(missing_ok=True)
		finally:
			sock.close()

	# Clean up old ~/.browser-use/run/ directory (stale PID/socket files)
	old_run_dir = Path.home() / '.browser-use' / 'run'
	if old_run_dir.is_dir():
		for stale_file in old_run_dir.glob('browser-use-*'):
			stale_file.unlink(missing_ok=True)
		# Remove the directory if empty
		try:
			old_run_dir.rmdir()
		except OSError:
			pass