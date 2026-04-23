def get_custom_params_from_lr(lr: LogIterable, initial_state: str = "first") -> dict[str, Any]:
  """
  Use this to get custom params dict based on provided logs.
  Useful when replaying following processes: calibrationd, paramsd, torqued
  The params may be based on first or last message of given type (carParams, liveCalibration, liveParameters, liveTorqueParameters) in the logs.
  """

  car_params = [m for m in lr if m.which() == "carParams"]
  live_calibration = [m for m in lr if m.which() == "liveCalibration"]
  live_parameters = [m for m in lr if m.which() == "liveParameters"]
  live_torque_parameters = [m for m in lr if m.which() == "liveTorqueParameters"]

  assert initial_state in ["first", "last"]
  msg_index = 0 if initial_state == "first" else -1

  assert len(car_params) > 0, "carParams required for initial state of liveParameters and CarParamsPrevRoute"
  CP = car_params[msg_index].carParams

  custom_params = {
    "CarParamsPrevRoute": CP.as_builder().to_bytes()
  }

  if len(live_calibration) > 0:
    custom_params["CalibrationParams"] = live_calibration[msg_index].as_builder().to_bytes()
  if len(live_parameters) > 0:
    custom_params["LiveParametersV2"] = live_parameters[msg_index].as_builder().to_bytes()
  if len(live_torque_parameters) > 0:
    custom_params["LiveTorqueParameters"] = live_torque_parameters[msg_index].as_builder().to_bytes()

  return custom_params