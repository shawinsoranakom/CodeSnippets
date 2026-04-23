async def run(self) -> None:
		"""Listen on Unix socket (or TCP on Windows) with PID file.

		Note: we do NOT unlink the socket in our finally block. If a replacement
		daemon was spawned during our shutdown, it already bound a new socket at
		the same path — unlinking here would delete *its* socket, orphaning it.
		Stale sockets are cleaned up by is_daemon_alive() and by the next
		daemon's startup (unlink before bind).
		"""
		import secrets

		from browser_use.skill_cli.utils import get_auth_token_path, get_pid_path, get_socket_path

		self._write_state('initializing')

		# Generate and persist a per-session auth token.
		# The client reads this file to authenticate its requests, preventing
		# any other local process from sending commands to the daemon socket.
		# Create the temp file with 0o600 at open() time to avoid a permission
		# race window where the file exists but is not yet restricted.
		# Raise on failure — running without a readable token file leaves the
		# daemon permanently unauthorized for all clients.
		self._auth_token = secrets.token_hex(32)
		token_path = get_auth_token_path(self.session)
		tmp_token = token_path.with_suffix('.token.tmp')
		fd = os.open(str(tmp_token), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
		try:
			with os.fdopen(fd, 'w') as f:
				f.write(self._auth_token)
		except OSError:
			try:
				tmp_token.unlink(missing_ok=True)
			except OSError:
				pass
			raise
		os.replace(tmp_token, token_path)

		# Setup signal handlers
		loop = asyncio.get_running_loop()

		def signal_handler():
			self._request_shutdown()

		for sig in (signal.SIGINT, signal.SIGTERM):
			try:
				loop.add_signal_handler(sig, signal_handler)
			except NotImplementedError:
				pass  # Windows doesn't support add_signal_handler

		if hasattr(signal, 'SIGHUP'):
			try:
				loop.add_signal_handler(signal.SIGHUP, signal_handler)
			except NotImplementedError:
				pass

		sock_path = get_socket_path(self.session)
		pid_path = get_pid_path(self.session)
		logger.info(f'Session: {self.session}, Socket: {sock_path}')

		if sock_path.startswith('tcp://'):
			# Windows: TCP server
			_, hostport = sock_path.split('://', 1)
			host, port = hostport.split(':')
			self._server = await asyncio.start_server(
				self.handle_connection,
				host,
				int(port),
				reuse_address=True,
			)
			logger.info(f'Listening on TCP {host}:{port}')
		else:
			# Unix: socket server
			Path(sock_path).unlink(missing_ok=True)
			self._server = await asyncio.start_unix_server(
				self.handle_connection,
				sock_path,
			)
			logger.info(f'Listening on Unix socket {sock_path}')

		# Write PID file after server is bound
		my_pid = str(os.getpid())
		pid_path.write_text(my_pid)
		self._write_state('ready')

		try:
			async with self._server:
				await self._shutdown_event.wait()
				# Wait for shutdown to finish browser cleanup before exiting
				if self._shutdown_task:
					await self._shutdown_task
		except asyncio.CancelledError:
			pass
		finally:
			# Conditionally delete PID file only if it still contains our PID
			try:
				if pid_path.read_text().strip() == my_pid:
					pid_path.unlink(missing_ok=True)
			except (OSError, ValueError):
				pass
			logger.info('Daemon stopped')