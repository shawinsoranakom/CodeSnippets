def _kill_process(pid: int) -> bool:
	"""Kill a process by PID. Returns True if killed, False if already dead."""
	import time

	if sys.platform == 'win32':
		import ctypes

		PROCESS_TERMINATE = 0x0001
		handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
		if not handle:
			return False
		try:
			ctypes.windll.kernel32.TerminateProcess(handle, 1)
			for _ in range(10):
				if not _is_process_alive(pid):
					return True
				time.sleep(0.1)
			return not _is_process_alive(pid)
		finally:
			ctypes.windll.kernel32.CloseHandle(handle)
	else:
		try:
			os.kill(pid, signal.SIGTERM)
			for _ in range(10):
				if not _is_process_alive(pid):
					return True
				time.sleep(0.1)
			# Force kill if still alive
			os.kill(pid, signal.SIGKILL)
			return True
		except (OSError, ProcessLookupError):
			return False