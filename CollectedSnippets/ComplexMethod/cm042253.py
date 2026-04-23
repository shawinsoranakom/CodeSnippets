def test_panda_safety_carstate_fuzzy(self, data):
    """
      For each example, pick a random CAN message on the bus and fuzz its data,
      checking for panda state mismatches.
    """

    if self.CP.dashcamOnly:
      self.skipTest("no need to check panda safety for dashcamOnly")

    valid_addrs = [(addr, bus, size) for bus, addrs in self.fingerprint.items() for addr, size in addrs.items()]
    address, bus, size = data.draw(st.sampled_from(valid_addrs))

    msg_strategy = st.binary(min_size=size, max_size=size)
    msgs = data.draw(st.lists(msg_strategy, min_size=20))

    vehicle_speed_seen = self.CP.steerControlType == SteerControlType.angle and not self.CP.notCar

    for n, dat in enumerate(msgs):
      # due to panda updating state selectively, only edges are expected to match
      # TODO: warm up CarState with real CAN messages to check edge of both sources
      #  (eg. toyota's gasPressed is the inverse of a signal being set)
      prev_panda_gas = self.safety.get_gas_pressed_prev()
      prev_panda_brake = self.safety.get_brake_pressed_prev()
      prev_panda_regen_braking = self.safety.get_regen_braking_prev()
      prev_panda_steering_disengage = self.safety.get_steering_disengage_prev()
      prev_panda_vehicle_moving = self.safety.get_vehicle_moving()
      prev_panda_vehicle_speed_min = self.safety.get_vehicle_speed_min()
      prev_panda_vehicle_speed_max = self.safety.get_vehicle_speed_max()
      prev_panda_cruise_engaged = self.safety.get_cruise_engaged_prev()
      prev_panda_acc_main_on = self.safety.get_acc_main_on()

      to_send = libsafety_py.make_CANPacket(address, bus, dat)
      self.safety.safety_rx_hook(to_send)

      can = [(int(time.monotonic() * 1e9), [CanData(address=address, dat=dat, src=bus)])]
      CS = self.CI.update(can)
      if n < 5:  # CANParser warmup time
        continue

      if self.safety.get_gas_pressed_prev() != prev_panda_gas:
        self.assertEqual(CS.gasPressed, self.safety.get_gas_pressed_prev())

      if self.safety.get_brake_pressed_prev() != prev_panda_brake:
        # TODO: remove this exception once this mismatch is resolved
        brake_pressed = CS.brakePressed
        if CS.brakePressed and not self.safety.get_brake_pressed_prev():
          if self.CP.carFingerprint in (HONDA.HONDA_PILOT, HONDA.HONDA_RIDGELINE) and CS.brake > 0.05:
            brake_pressed = False

        self.assertEqual(brake_pressed, self.safety.get_brake_pressed_prev())

      if self.safety.get_regen_braking_prev() != prev_panda_regen_braking:
        self.assertEqual(CS.regenBraking, self.safety.get_regen_braking_prev())

      if self.safety.get_steering_disengage_prev() != prev_panda_steering_disengage:
        self.assertEqual(CS.steeringDisengage, self.safety.get_steering_disengage_prev())

      if self.safety.get_vehicle_moving() != prev_panda_vehicle_moving and not self.CP.notCar:
        self.assertEqual(not CS.standstill, self.safety.get_vehicle_moving())

      # check vehicle speed if angle control car or available
      if self.safety.get_vehicle_speed_min() > 0 or self.safety.get_vehicle_speed_max() > 0:
        vehicle_speed_seen = True

      if vehicle_speed_seen and (self.safety.get_vehicle_speed_min() != prev_panda_vehicle_speed_min or
                                 self.safety.get_vehicle_speed_max() != prev_panda_vehicle_speed_max):
        v_ego_raw = CS.vEgoRaw / self.CP.wheelSpeedFactor
        self.assertFalse(v_ego_raw > (self.safety.get_vehicle_speed_max() + 1e-3) or
                         v_ego_raw < (self.safety.get_vehicle_speed_min() - 1e-3))

      if not (self.CP.brand == "honda" and not (self.CP.flags & HondaFlags.BOSCH)):
        if self.safety.get_cruise_engaged_prev() != prev_panda_cruise_engaged:
          self.assertEqual(CS.cruiseState.enabled, self.safety.get_cruise_engaged_prev())

      if self.CP.brand == "honda":
        if self.safety.get_acc_main_on() != prev_panda_acc_main_on:
          self.assertEqual(CS.cruiseState.available, self.safety.get_acc_main_on())