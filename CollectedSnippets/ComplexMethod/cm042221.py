def migrate_pandaStates(msgs):
  # TODO: safety param migration should be handled automatically
  safety_param_migration = {
    "TOYOTA_PRIUS": EPS_SCALE["TOYOTA_PRIUS"] | ToyotaSafetyFlags.STOCK_LONGITUDINAL,
    "TOYOTA_RAV4": EPS_SCALE["TOYOTA_RAV4"] | ToyotaSafetyFlags.ALT_BRAKE,
    "KIA_EV6": HyundaiSafetyFlags.EV_GAS | HyundaiSafetyFlags.CANFD_LKA_STEER_MSG,
    "CHEVROLET_VOLT": GMSafetyFlags.EV,
    "CHEVROLET_BOLT_EUV": GMSafetyFlags.EV | GMSafetyFlags.HW_CAM,
  }
  # TODO: get new Ford route
  safety_param_migration |= dict.fromkeys((set(FORD) - FORD.with_flags(FordFlags.CANFD)), FordSafetyFlags.LONG_CONTROL)

  # Migrate safety param base on carParams
  CP = next((m.carParams for _, m in msgs if m.which() == 'carParams'), None)
  assert CP is not None, "carParams message not found"
  fingerprint = MIGRATION.get(CP.carFingerprint, CP.carFingerprint)
  if fingerprint in safety_param_migration:
    safety_param = safety_param_migration[fingerprint].value
  elif len(CP.safetyConfigs):
    safety_param = CP.safetyConfigs[0].safetyParam
    if CP.safetyConfigs[0].safetyParamDEPRECATED != 0:
      safety_param = CP.safetyConfigs[0].safetyParamDEPRECATED
  else:
    safety_param = CP.safetyParamDEPRECATED

  ops = []
  for index, msg in msgs:
    if msg.which() == 'pandaStateDEPRECATED':
      new_msg = messaging.new_message('pandaStates', 1)
      new_msg.valid = msg.valid
      new_msg.logMonoTime = msg.logMonoTime
      new_msg.pandaStates[0] = msg.pandaStateDEPRECATED
      new_msg.pandaStates[0].safetyParam = safety_param
      ops.append((index, new_msg.as_reader()))
    elif msg.which() == 'pandaStates':
      new_msg = msg.as_builder()
      new_msg.pandaStates[-1].safetyParam = safety_param
      # Clear DISABLE_DISENGAGE_ON_GAS bit to fix controls mismatch
      new_msg.pandaStates[-1].alternativeExperience &= ~1
      ops.append((index, new_msg.as_reader()))
  return ops, [], []