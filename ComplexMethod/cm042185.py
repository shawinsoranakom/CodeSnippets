def main():
  config_realtime_process([0, 1, 2, 3], 5)

  DEBUG = bool(int(os.getenv("DEBUG", "0")))

  pm = messaging.PubMaster(['liveDelay'])
  sm = messaging.SubMaster(['livePose', 'liveCalibration', 'carState', 'controlsState', 'carControl'], poll='livePose')

  params = Params()
  CP = messaging.log_from_bytes(params.get("CarParams", block=True), car.CarParams)

  lag_learner = LateralLagEstimator(CP, 1. / SERVICE_LIST['livePose'].frequency)
  if (initial_lag_params := retrieve_initial_lag(params, CP)) is not None:
    lag, valid_blocks = initial_lag_params
    lag_learner.reset(lag, valid_blocks)

  while True:
    sm.update()
    if sm.all_checks():
      for which in sorted(sm.updated.keys(), key=lambda x: sm.logMonoTime[x]):
        if sm.updated[which]:
          t = sm.logMonoTime[which] * 1e-9
          lag_learner.handle_log(t, which, sm[which])
      lag_learner.update_points()

    # 4Hz driven by livePose
    if sm.frame % 5 == 0:
      lag_learner.update_estimate()
      lag_msg = lag_learner.get_msg(sm.all_checks(), DEBUG)
      lag_msg_dat = lag_msg.to_bytes()
      pm.send('liveDelay', lag_msg_dat)

      if sm.frame % 1200 == 0: # cache every 60 seconds
        params.put_nonblocking("LiveDelay", lag_msg_dat)