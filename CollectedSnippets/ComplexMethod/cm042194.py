def retrieve_initial_vehicle_params(params: Params, CP: car.CarParams, replay: bool, debug: bool):
  last_parameters_data = params.get("LiveParametersV2")
  last_carparams_data = params.get("CarParamsPrevRoute")

  steer_ratio, stiffness_factor, angle_offset_deg, p_initial = CP.steerRatio, 1.0, 0.0, None

  retrieve_success = False
  if last_parameters_data is not None and last_carparams_data is not None:
    try:
      with log.Event.from_bytes(last_parameters_data) as last_lp_msg, car.CarParams.from_bytes(last_carparams_data) as last_CP:
        lp = last_lp_msg.liveParameters
        # Check if car model matches
        if last_CP.carFingerprint != CP.carFingerprint:
          raise Exception("Car model mismatch")

        # Check if starting values are sane
        min_sr, max_sr = 0.5 * CP.steerRatio, 2.0 * CP.steerRatio
        steer_ratio_sane = min_sr <= lp.steerRatio <= max_sr
        if not steer_ratio_sane:
          raise Exception(f"Invalid starting values found {lp}")

        initial_filter_std = np.array(lp.debugFilterState.std)
        if debug and len(initial_filter_std) != 0:
          p_initial = np.diag(initial_filter_std)

        steer_ratio, stiffness_factor, angle_offset_deg = lp.steerRatio, lp.stiffnessFactor, lp.angleOffsetAverageDeg
        retrieve_success = True
    except Exception as e:
      cloudlog.error(f"Failed to retrieve initial values: {e}")
      params.remove("LiveParametersV2")

  if not replay:
    # When driving in wet conditions the stiffness can go down, and then be too low on the next drive
    # Without a way to detect this we have to reset the stiffness every drive
    stiffness_factor = 1.0

  if not retrieve_success:
    cloudlog.info("Parameter learner resetting to default values")

  return steer_ratio, stiffness_factor, angle_offset_deg, p_initial