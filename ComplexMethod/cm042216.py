def model_replay(lr, frs):
  # modeld is using frame pairs
  modeld_logs = trim_logs(lr, START_FRAME, END_FRAME, {"roadCameraState", "wideRoadCameraState"},
                                                                         {"roadEncodeIdx", "wideRoadEncodeIdx", "carParams", "carState", "carControl", "can"})
  dmodeld_logs = trim_logs(lr, START_FRAME, END_FRAME, {"driverCameraState"}, {"driverEncodeIdx", "carParams", "can"})

  if not SEND_EXTRA_INPUTS:
    modeld_logs = [msg for msg in modeld_logs if msg.which() != 'liveCalibration']
    dmodeld_logs = [msg for msg in dmodeld_logs if msg.which() != 'liveCalibration']

  # initial setup
  for s in ('liveCalibration', 'deviceState'):
    msg = next(msg for msg in lr if msg.which() == s).as_builder()
    msg.logMonoTime = lr[0].logMonoTime
    modeld_logs.insert(1, msg.as_reader())
    dmodeld_logs.insert(1, msg.as_reader())

  modeld = get_process_config("modeld")
  dmonitoringmodeld = get_process_config("dmonitoringmodeld")

  modeld_msgs = replay_process(modeld, modeld_logs, frs)
  dmonitoringmodeld_msgs = replay_process(dmonitoringmodeld, dmodeld_logs, frs)

  msgs = modeld_msgs + dmonitoringmodeld_msgs

  header = ['model', 'max instant', 'max instant allowed', 'average', 'max average allowed', 'test result']
  rows = []
  timings_ok = True
  for (s, instant_max, avg_max) in EXEC_TIMINGS:
    ts = [getattr(m, s).modelExecutionTime for m in msgs if m.which() == s]
    # TODO some init can happen in first iteration
    ts = ts[1:]

    errors = []
    if np.max(ts) > instant_max:
      errors.append("❌ FAILED MAX TIMING CHECK ❌")
    if np.mean(ts) > avg_max:
      errors.append("❌ FAILED AVG TIMING CHECK ❌")

    timings_ok = not errors and timings_ok
    rows.append([s, np.max(ts), instant_max, np.mean(ts), avg_max, "\n".join(errors) or "✅"])

  print("------------------------------------------------")
  print("----------------- Model Timing -----------------")
  print("------------------------------------------------")
  print(tabulate(rows, header, tablefmt="simple_grid", stralign="center", numalign="center", floatfmt=".4f"))
  assert timings_ok or PC

  return msgs