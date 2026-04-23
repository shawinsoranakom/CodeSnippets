def get_testing_data_from_logreader(cls, lr):
    car_fw = []
    can_msgs = []
    cls.elm_frame = None
    cls.car_safety_mode_frame = None
    cls.fingerprint = gen_empty_fingerprint()
    alpha_long = False
    for msg in lr:
      if msg.which() == "can":
        can = can_capnp_to_list((msg.as_builder().to_bytes(),))[0]
        can_msgs.append((can[0], [CanData(*can) for can in can[1]]))
        if len(can_msgs) <= FRAME_FINGERPRINT:
          for m in msg.can:
            if m.src < 64:
              cls.fingerprint[m.src][m.address] = len(m.dat)

      elif msg.which() == "carParams":
        car_fw = msg.carParams.carFw
        if msg.carParams.openpilotLongitudinalControl:
          alpha_long = True
        if cls.platform is None:
          live_fingerprint = msg.carParams.carFingerprint
          cls.platform = MIGRATION.get(live_fingerprint, live_fingerprint)

      # Log which can frame the panda safety mode left ELM327, for CAN validity checks
      elif msg.which() == 'pandaStates':
        for ps in msg.pandaStates:
          if cls.elm_frame is None and ps.safetyModel != SafetyModel.elm327:
            cls.elm_frame = len(can_msgs)
          if cls.car_safety_mode_frame is None and ps.safetyModel not in \
            (SafetyModel.elm327, SafetyModel.noOutput):
            cls.car_safety_mode_frame = len(can_msgs)

      elif msg.which() == 'pandaStateDEPRECATED':
        if cls.elm_frame is None and msg.pandaStateDEPRECATED.safetyModel != SafetyModel.elm327:
          cls.elm_frame = len(can_msgs)
        if cls.car_safety_mode_frame is None and msg.pandaStateDEPRECATED.safetyModel not in \
          (SafetyModel.elm327, SafetyModel.noOutput):
          cls.car_safety_mode_frame = len(can_msgs)

    assert len(can_msgs) > int(50 / DT_CTRL), "no can data found"
    return car_fw, can_msgs, alpha_long