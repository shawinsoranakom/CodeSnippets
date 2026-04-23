def discover_chrome_cdp_url() -> str:
	"""Auto-discover a running Chrome instance's CDP WebSocket URL.

	Strategy:
	1. Read ``DevToolsActivePort`` from known Chrome data dirs.
	2. Probe ``/json/version`` via HTTP to get ``webSocketDebuggerUrl``.
	3. If HTTP fails, construct ``ws://`` URL directly from the port file.
	4. Fallback: probe well-known port 9222.

	Raises ``RuntimeError`` if no running Chrome with remote debugging is found.
	"""

	def _probe_http(port: int) -> str | None:
		"""Try GET http://127.0.0.1:{port}/json/version and return webSocketDebuggerUrl."""
		try:
			req = urllib.request.Request(f'http://127.0.0.1:{port}/json/version')
			with urllib.request.urlopen(req, timeout=2) as resp:
				data = _json.loads(resp.read())
				url = data.get('webSocketDebuggerUrl')
				if url and isinstance(url, str):
					return url
		except Exception:
			pass
		return None

	def _port_is_open(port: int) -> bool:
		"""Check if something is listening on 127.0.0.1:{port}."""
		import socket

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			s.settimeout(1)
			s.connect(('127.0.0.1', port))
			return True
		except OSError:
			return False
		finally:
			s.close()

	# --- Phase 1: DevToolsActivePort files ---
	for data_dir in get_chrome_user_data_dirs():
		port_file = data_dir / 'DevToolsActivePort'
		if not port_file.is_file():
			continue
		try:
			lines = port_file.read_text().strip().splitlines()
			if not lines:
				continue
			port = int(lines[0].strip())
			ws_path = lines[1].strip() if len(lines) > 1 else '/devtools/browser'
		except (ValueError, OSError):
			continue

		# Try HTTP probe first (gives us the full canonical URL)
		ws_url = _probe_http(port)
		if ws_url:
			return ws_url

		# HTTP may not respond (Chrome M144+), but if the port is open, trust the file
		if _port_is_open(port):
			return f'ws://127.0.0.1:{port}{ws_path}'

	# --- Phase 2: well-known fallback ports ---
	for port in (9222,):
		ws_url = _probe_http(port)
		if ws_url:
			return ws_url

	raise RuntimeError(
		'Could not discover a running Chrome instance with remote debugging enabled.\n'
		'Enable remote debugging in Chrome (chrome://inspect/#remote-debugging, or launch with --remote-debugging-port=9222) and try again.'
	)