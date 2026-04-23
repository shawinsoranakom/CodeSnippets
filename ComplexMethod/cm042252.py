def test_panda_safety_rx_checks(self):
    if self.CP.dashcamOnly:
      self.skipTest("no need to check panda safety for dashcamOnly")

    start_ts = self.can_msgs[0][0]

    failed_addrs = Counter()
    for can in self.can_msgs:
      # update panda timer
      t = (can[0] - start_ts) / 1e3
      self.safety.set_timer(int(t))

      # run all msgs through the safety RX hook
      for msg in can[1]:
        if msg.src >= 64:
          continue

        to_send = libsafety_py.make_CANPacket(msg.address, msg.src % 4, msg.dat)
        if self.safety.safety_rx_hook(to_send) != 1:
          failed_addrs[hex(msg.address)] += 1

      # ensure all msgs defined in the addr checks are valid
      self.safety.safety_tick_current_safety_config()
      if t > 1e6:
        self.assertTrue(self.safety.safety_config_valid())

      # Don't check relay malfunction on disabled routes (relay closed),
      # or before fingerprinting is done (elm327 and noOutput)
      if self.openpilot_enabled and t / 1e4 > self.car_safety_mode_frame:
        self.assertFalse(self.safety.get_relay_malfunction())
      else:
        self.safety.set_relay_malfunction(False)

    self.assertFalse(len(failed_addrs), f"panda safety RX check failed: {failed_addrs}")

    # ensure RX checks go invalid after small time with no traffic
    self.safety.set_timer(int(t + (2*1e6)))
    self.safety.safety_tick_current_safety_config()
    self.assertFalse(self.safety.safety_config_valid())