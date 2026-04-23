def get_car_params_callback(rc, pm, msgs, fingerprint):
  params = Params()
  if fingerprint:
    CarInterface = interfaces[fingerprint]
    CP = CarInterface.get_non_essential_params(fingerprint)
  else:
    can_msgs = ([CanData(can.address, can.dat, can.src) for can in m.can] for m in msgs if m.which() == "can")
    cached_params_raw = params.get("CarParamsCache")
    assert next(can_msgs, None), "CAN messages are required for fingerprinting"
    assert os.environ.get("SKIP_FW_QUERY", False) or cached_params_raw is not None, \
            "CarParamsCache is required for fingerprinting. Make sure to keep carParams msgs in the logs."

    def can_recv(wait_for_one: bool = False) -> list[list[CanData]]:
      return [next(can_msgs, [])]

    cached_params = None
    if cached_params_raw is not None:
      with car.CarParams.from_bytes(cached_params_raw) as _cached_params:
        cached_params = _cached_params

    CP = get_car(can_recv, lambda _msgs: None, lambda obd: None, params.get_bool("AlphaLongitudinalEnabled"), False, cached_params=cached_params).CP

  params.put("CarParams", CP.to_bytes())