def ensure_running(procs: ValuesView[ManagerProcess], started: bool, params=None, CP: car.CarParams=None,
                   not_run: list[str] | None=None) -> list[ManagerProcess]:
  if not_run is None:
    not_run = []

  running = []
  for p in procs:
    if p.enabled and p.name not in not_run and p.should_run(started, params, CP):
      if p.restart_if_crash and p.proc is not None and not p.proc.is_alive():
        cloudlog.error(f'Restarting {p.name} (exitcode {p.proc.exitcode})')
        p.restart()
      running.append(p)
    else:
      p.stop(block=False)

  for p in running:
    p.start()

  return running