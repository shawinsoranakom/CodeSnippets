def processes_context(processes, init_time=0, ignore_stopped=None):
  ignore_stopped = [] if ignore_stopped is None else ignore_stopped

  # start and assert started
  for n, p in enumerate(processes):
    managed_processes[p].start()
    if n < len(processes) - 1:
      time.sleep(init_time)

  assert all(managed_processes[name].proc.exitcode is None for name in processes)

  try:
    yield [managed_processes[name] for name in processes]
    # assert processes are still started
    assert all(managed_processes[name].proc.exitcode is None for name in processes if name not in ignore_stopped)
  finally:
    for p in processes:
      managed_processes[p].stop()