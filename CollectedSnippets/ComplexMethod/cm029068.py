def is_running_in_docker() -> bool:
	"""Detect if we are running in a docker container, for the purpose of optimizing chrome launch flags (dev shm usage, gpu settings, etc.)"""
	try:
		if Path('/.dockerenv').exists() or 'docker' in Path('/proc/1/cgroup').read_text().lower():
			return True
	except Exception:
		pass

	try:
		# if init proc (PID 1) looks like uvicorn/python/uv/etc. then we're in Docker
		# if init proc (PID 1) looks like bash/systemd/init/etc. then we're probably NOT in Docker
		init_cmd = ' '.join(psutil.Process(1).cmdline())
		if ('py' in init_cmd) or ('uv' in init_cmd) or ('app' in init_cmd):
			return True
	except Exception:
		pass

	try:
		# if less than 10 total running procs, then we're almost certainly in a container
		if len(psutil.pids()) < 10:
			return True
	except Exception:
		pass

	return False