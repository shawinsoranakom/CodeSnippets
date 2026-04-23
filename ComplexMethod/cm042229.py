def generate_params_config(lr=None, CP=None, fingerprint=None, custom_params=None) -> dict[str, Any]:
  params_dict = {
    "OpenpilotEnabledToggle": True,
    "DisengageOnAccelerator": True,
    "DisableLogging": False,
  }

  if custom_params is not None:
    params_dict.update(custom_params)
  if lr is not None:
    has_ublox = any(msg.which() == "ubloxGnss" for msg in lr)
    params_dict["UbloxAvailable"] = has_ublox
    is_rhd = next((msg.driverMonitoringState.isRHD for msg in lr if msg.which() == "driverMonitoringState"), False)
    params_dict["IsRhdDetected"] = is_rhd

  if CP is not None:
    if fingerprint is None:
      if CP.fingerprintSource == "fw":
        params_dict["CarParamsCache"] = CP.as_builder().to_bytes()

    if CP.openpilotLongitudinalControl:
      params_dict["AlphaLongitudinalEnabled"] = True

    if CP.notCar:
      params_dict["JoystickDebugMode"] = True

  return params_dict