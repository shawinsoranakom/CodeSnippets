def find_events(lr: LogReader, extrapolate: bool = False, qlog: bool = False) -> list[Event]:
  min_lat_active = RLOG_MIN_LAT_ACTIVE // QLOG_DECIMATION if qlog else RLOG_MIN_LAT_ACTIVE
  min_steering_unpressed = RLOG_MIN_STEERING_UNPRESSED // QLOG_DECIMATION if qlog else RLOG_MIN_STEERING_UNPRESSED
  min_requesting_max = RLOG_MIN_REQUESTING_MAX // QLOG_DECIMATION if qlog else RLOG_MIN_REQUESTING_MAX

  # if we test with driver torque safety, max torque can be slightly noisy
  steer_threshold = 0.7 if extrapolate else 0.95

  events = []

  # state tracking
  steering_unpressed = 0  # frames
  requesting_max = 0  # frames
  lat_active = 0  # frames

  # current state
  curvature = 0
  v_ego = 0
  roll = 0
  out_torque = 0

  start_ts = 0
  for msg in lr:
    if msg.which() == 'carControl':
      if start_ts == 0:
        start_ts = msg.logMonoTime

      lat_active = lat_active + 1 if msg.carControl.latActive else 0

    elif msg.which() == 'carOutput':
      out_torque = msg.carOutput.actuatorsOutput.torque
      requesting_max = requesting_max + 1 if abs(out_torque) > steer_threshold else 0

    elif msg.which() == 'carState':
      steering_unpressed = steering_unpressed + 1 if not msg.carState.steeringPressed else 0
      v_ego = msg.carState.vEgo

    elif msg.which() == 'controlsState':
      curvature = msg.controlsState.curvature

    elif msg.which() == 'liveParameters':
      roll = msg.liveParameters.roll

    if lat_active > min_lat_active and steering_unpressed > min_steering_unpressed and requesting_max > min_requesting_max:
      # TODO: record max lat accel at the end of the event, need to use the past lat accel as overriding can happen before we detect it
      requesting_max = 0

      factor = 1 / abs(out_torque)
      current_lateral_accel = (curvature * v_ego ** 2 * factor) - roll * EARTH_G
      events.append(Event(current_lateral_accel, v_ego, roll, round((msg.logMonoTime - start_ts) * 1e-9, 2)))
      print(events[-1])

  return events