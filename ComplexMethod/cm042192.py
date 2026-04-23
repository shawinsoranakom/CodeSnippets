def __init__(self, CP, decimated=False, track_all_points=False):
    self.hist_len = int(HISTORY / DT_MDL)
    self.lag = 0.0
    self.track_all_points = track_all_points  # for offline analysis, without max lateral accel or max steer torque filters
    if decimated:
      self.min_bucket_points = MIN_BUCKET_POINTS / 10
      self.min_points_total = MIN_POINTS_TOTAL_QLOG
      self.fit_points = FIT_POINTS_TOTAL_QLOG
      self.factor_sanity = FACTOR_SANITY_QLOG
      self.friction_sanity = FRICTION_SANITY_QLOG

    else:
      self.min_bucket_points = MIN_BUCKET_POINTS
      self.min_points_total = MIN_POINTS_TOTAL
      self.fit_points = FIT_POINTS_TOTAL
      self.factor_sanity = FACTOR_SANITY
      self.friction_sanity = FRICTION_SANITY

    self.offline_friction = 0.0
    self.offline_latAccelFactor = 0.0
    self.resets = 0.0
    self.use_params = CP.brand in ALLOWED_CARS and CP.lateralTuning.which() == 'torque'

    if CP.lateralTuning.which() == 'torque':
      self.offline_friction = CP.lateralTuning.torque.friction
      self.offline_latAccelFactor = CP.lateralTuning.torque.latAccelFactor

    self.calibrator = PoseCalibrator()

    self.reset()

    initial_params = {
      'latAccelFactor': self.offline_latAccelFactor,
      'latAccelOffset': 0.0,
      'frictionCoefficient': self.offline_friction,
      'points': []
    }
    self.decay = MIN_FILTER_DECAY
    self.min_lataccel_factor = (1.0 - self.factor_sanity) * self.offline_latAccelFactor
    self.max_lataccel_factor = (1.0 + self.factor_sanity) * self.offline_latAccelFactor
    self.min_friction = (1.0 - self.friction_sanity) * self.offline_friction
    self.max_friction = (1.0 + self.friction_sanity) * self.offline_friction

    # try to restore cached params
    params = Params()
    params_cache = params.get("CarParamsPrevRoute")
    torque_cache = params.get("LiveTorqueParameters")
    if params_cache is not None and torque_cache is not None:
      try:
        with log.Event.from_bytes(torque_cache) as log_evt:
          cache_ltp = log_evt.liveTorqueParameters
        with car.CarParams.from_bytes(params_cache) as msg:
          cache_CP = msg
        if self.get_restore_key(cache_CP, cache_ltp.version) == self.get_restore_key(CP, VERSION):
          if cache_ltp.liveValid:
            initial_params = {
              'latAccelFactor': cache_ltp.latAccelFactorFiltered,
              'latAccelOffset': cache_ltp.latAccelOffsetFiltered,
              'frictionCoefficient': cache_ltp.frictionCoefficientFiltered
            }
          initial_params['points'] = cache_ltp.points
          self.decay = cache_ltp.decay
          self.filtered_points.load_points(initial_params['points'])
          cloudlog.info("restored torque params from cache")
      except Exception:
        cloudlog.exception("failed to restore cached torque params")
        params.remove("LiveTorqueParameters")

    self.filtered_params = {}
    for param in initial_params:
      self.filtered_params[param] = FirstOrderFilter(initial_params[param], self.decay, DT_MDL)