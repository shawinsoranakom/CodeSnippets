def test_panda_safety_carstate(self):
    """
      Assert that panda safety matches openpilot's carState
    """
    if self.CP.dashcamOnly:
      self.skipTest("no need to check panda safety for dashcamOnly")

    # warm up pass, as initial states may be different
    for can in self.can_msgs[:300]:
      self.CI.update(can)
      for msg in filter(lambda m: m.src < 64, can[1]):
        to_send = libsafety_py.make_CANPacket(msg.address, msg.src % 4, msg.dat)
        self.safety.safety_rx_hook(to_send)

    controls_allowed_prev = False
    CS_prev = car.CarState.new_message()
    checks = defaultdict(int)
    vehicle_speed_seen = self.CP.steerControlType == SteerControlType.angle and not self.CP.notCar
    for idx, can in enumerate(self.can_msgs):
      CS = self.CI.update(can).as_reader()
      for msg in filter(lambda m: m.src < 64, can[1]):
        to_send = libsafety_py.make_CANPacket(msg.address, msg.src % 4, msg.dat)
        ret = self.safety.safety_rx_hook(to_send)
        self.assertEqual(1, ret, f"safety rx failed ({ret=}): {(msg.address, msg.src % 4)}")

      # Skip first frame so CS_prev is properly initialized
      if idx == 0:
        CS_prev = CS
        # Button may be left pressed in warm up period
        if not self.CP.pcmCruise:
          self.safety.set_controls_allowed(0)
        continue

      # TODO: check rest of panda's carstate (steering, ACC main on, etc.)

      checks['gasPressed'] += CS.gasPressed != self.safety.get_gas_pressed_prev()
      checks['standstill'] += (CS.standstill == self.safety.get_vehicle_moving()) and not self.CP.notCar

      # check vehicle speed if angle control car or available
      if self.safety.get_vehicle_speed_min() > 0 or self.safety.get_vehicle_speed_max() > 0:
        vehicle_speed_seen = True

      if vehicle_speed_seen:
        v_ego_raw = CS.vEgoRaw / self.CP.wheelSpeedFactor
        checks['vEgoRaw'] += (v_ego_raw > (self.safety.get_vehicle_speed_max() + 1e-3) or
                              v_ego_raw < (self.safety.get_vehicle_speed_min() - 1e-3))

      # TODO: remove this exception once this mismatch is resolved
      brake_pressed = CS.brakePressed
      if CS.brakePressed and not self.safety.get_brake_pressed_prev():
        if self.CP.carFingerprint in (HONDA.HONDA_PILOT, HONDA.HONDA_RIDGELINE) and CS.brake > 0.05:
          brake_pressed = False
      checks['brakePressed'] += brake_pressed != self.safety.get_brake_pressed_prev()
      checks['regenBraking'] += CS.regenBraking != self.safety.get_regen_braking_prev()
      checks['steeringDisengage'] += CS.steeringDisengage != self.safety.get_steering_disengage_prev()

      if self.CP.pcmCruise:
        # On most pcmCruise cars, openpilot's state is always tied to the PCM's cruise state.
        # On Honda Nidec, we always engage on the rising edge of the PCM cruise state, but
        # openpilot brakes to zero even if the min ACC speed is non-zero (i.e. the PCM disengages).
        if self.CP.brand == "honda" and not (self.CP.flags & HondaFlags.BOSCH):
          # only the rising edges are expected to match
          if CS.cruiseState.enabled and not CS_prev.cruiseState.enabled:
            checks['controlsAllowed'] += not self.safety.get_controls_allowed()
        else:
          checks['controlsAllowed'] += not CS.cruiseState.enabled and self.safety.get_controls_allowed()

        # TODO: fix notCar mismatch
        if not self.CP.notCar:
          checks['cruiseState'] += CS.cruiseState.enabled != self.safety.get_cruise_engaged_prev()
      else:
        # Check for user button enable on rising edge of controls allowed
        button_enable = CS.buttonEnable and (not CS.brakePressed or CS.standstill)
        mismatch = button_enable != (self.safety.get_controls_allowed() and not controls_allowed_prev)
        checks['controlsAllowed'] += mismatch
        controls_allowed_prev = self.safety.get_controls_allowed()
        if button_enable and not mismatch:
          self.safety.set_controls_allowed(False)

      if self.CP.brand == "honda":
        checks['mainOn'] += CS.cruiseState.available != self.safety.get_acc_main_on()

      CS_prev = CS

    failed_checks = {k: v for k, v in checks.items() if v > 0}
    self.assertFalse(len(failed_checks), f"panda safety doesn't agree with openpilot: {failed_checks}")