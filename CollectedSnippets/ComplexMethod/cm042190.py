def main():
  config_realtime_process([0, 1, 2, 3], 5)

  DEBUG = bool(int(os.getenv("DEBUG", "0")))
  SIMULATION = bool(int(os.getenv("SIMULATION", "0")))

  pm = messaging.PubMaster(['livePose'])
  sm = messaging.SubMaster(['carState', 'liveCalibration', 'cameraOdometry'], poll='cameraOdometry')
  # separate sensor sockets for efficiency
  sensor_sockets = [messaging.sub_sock(which, timeout=20) for which in ['accelerometer', 'gyroscope']]
  sensor_alive, sensor_valid, sensor_recv_time = defaultdict(bool), defaultdict(bool), defaultdict(float)

  params = Params()

  estimator = LocationEstimator(DEBUG)

  filter_initialized = False
  critcal_services = ["accelerometer", "gyroscope", "cameraOdometry"]
  observation_input_invalid = defaultdict(int)

  input_invalid_limit = {s: round(INPUT_INVALID_LIMIT * (SERVICE_LIST[s].frequency / 20.)) for s in critcal_services}
  input_invalid_threshold = {s: input_invalid_limit[s] - 0.5 for s in critcal_services}
  input_invalid_decay = {s: calculate_invalid_input_decay(input_invalid_limit[s], INPUT_INVALID_RECOVERY, SERVICE_LIST[s].frequency) for s in critcal_services}

  initial_pose_data = params.get("LocationFilterInitialState")
  if initial_pose_data is not None:
    with log.Event.from_bytes(initial_pose_data) as lp_msg:
      filter_state = lp_msg.livePose.debugFilterState
      x_initial = np.array(filter_state.value, dtype=np.float64) if len(filter_state.value) != 0 else PoseKalman.initial_x
      P_initial = np.diag(np.array(filter_state.std, dtype=np.float64)) if len(filter_state.std) != 0 else PoseKalman.initial_P
      estimator.reset(None, x_initial, P_initial)

  while True:
    sm.update()

    acc_msgs, gyro_msgs = (messaging.drain_sock(sock) for sock in sensor_sockets)

    if filter_initialized:
      msgs = []
      for msg in acc_msgs + gyro_msgs:
        t, valid, which, data = msg.logMonoTime, msg.valid, msg.which(), getattr(msg, msg.which())
        msgs.append((t, valid, which, data))
      for which, updated in sm.updated.items():
        if not updated:
          continue
        t, valid, data = sm.logMonoTime[which], sm.valid[which], sm[which]
        msgs.append((t, valid, which, data))

      for log_mono_time, valid, which, msg in sorted(msgs, key=lambda x: x[0]):
        if valid:
          t = log_mono_time * 1e-9
          res = estimator.handle_log(t, which, msg)
          if which not in critcal_services:
            continue

          if res == HandleLogResult.TIMING_INVALID:
            cloudlog.warning(f"Observation {which} ignored due to failed timing check")
            observation_input_invalid[which] += 1
          elif res == HandleLogResult.INPUT_INVALID:
            cloudlog.warning(f"Observation {which} ignored due to failed sanity check")
            observation_input_invalid[which] += 1
          elif res == HandleLogResult.SUCCESS:
            observation_input_invalid[which] *= input_invalid_decay[which]
    else:
      filter_initialized = sm.all_checks() and sensor_all_checks(acc_msgs, gyro_msgs, sensor_valid, sensor_recv_time, sensor_alive, SIMULATION)

    if sm.updated["cameraOdometry"]:
      critical_service_inputs_valid = all(observation_input_invalid[s] < input_invalid_threshold[s] for s in critcal_services)
      inputs_valid = sm.all_valid() and critical_service_inputs_valid
      sensors_valid = sensor_all_checks(acc_msgs, gyro_msgs, sensor_valid, sensor_recv_time, sensor_alive, SIMULATION)

      msg = estimator.get_msg(sensors_valid, inputs_valid, filter_initialized)
      pm.send("livePose", msg)