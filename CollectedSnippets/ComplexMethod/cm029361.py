async def start_tunnel(port: int) -> dict[str, Any]:
	"""Start a cloudflare quick tunnel for a local port.

	The tunnel runs as a daemon process that survives CLI exit.

	Args:
		port: Local port to tunnel

	Returns:
		Dict with 'url' and 'port' on success, or 'error' on failure
	"""
	# Check if tunnel already exists for this port
	existing = _load_tunnel_info(port)
	if existing:
		return {'url': existing['url'], 'port': port, 'existing': True}

	# Get cloudflared binary
	try:
		tunnel_manager = get_tunnel_manager()
		cloudflared_binary = tunnel_manager.get_binary_path()
	except RuntimeError as e:
		return {'error': str(e)}

	# Create log file for cloudflared stderr (avoids SIGPIPE when parent exits)
	_tunnels_dir().mkdir(parents=True, exist_ok=True)
	log_file_path = _tunnels_dir() / f'{port}.log'
	log_file = open(log_file_path, 'w')  # noqa: ASYNC230

	# Spawn cloudflared as a daemon
	# - start_new_session / creationflags: survives parent exit
	# - stderr to file: avoids SIGPIPE when parent's pipe closes
	spawn_kwargs: dict[str, Any] = {}
	if sys.platform == 'win32':
		spawn_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
	else:
		spawn_kwargs['start_new_session'] = True

	process = await asyncio.create_subprocess_exec(
		cloudflared_binary,
		'tunnel',
		'--url',
		f'http://localhost:{port}',
		stdout=asyncio.subprocess.DEVNULL,
		stderr=log_file,
		**spawn_kwargs,
	)

	# Poll the log file until we find the tunnel URL
	url: str | None = None
	try:
		import time

		deadline = time.time() + 15
		while time.time() < deadline:
			# Check if process died
			if process.returncode is not None:
				log_file.close()
				content = log_file_path.read_text() if log_file_path.exists() else ''
				return {'error': f'cloudflared exited unexpectedly: {content[:500]}'}

			# Read log file content
			try:
				content = log_file_path.read_text()
				match = _URL_PATTERN.search(content)
				if match:
					url = match.group(1)
					break
			except OSError:
				pass

			await asyncio.sleep(0.2)
	except Exception as e:
		process.terminate()
		log_file.close()
		return {'error': f'Failed to start tunnel: {e}'}

	if url is None:
		process.terminate()
		log_file.close()
		return {'error': 'Timed out waiting for cloudflare tunnel URL (15s)'}

	# Close log file handle to avoid leaking file descriptors
	log_file.close()

	# Save tunnel info to disk so it persists across CLI invocations
	_save_tunnel_info(port, process.pid, url)
	logger.info(f'Tunnel started: localhost:{port} -> {url} (pid={process.pid})')

	return {'url': url, 'port': port}