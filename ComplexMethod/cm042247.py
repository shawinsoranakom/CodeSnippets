def update(self, CS: car.CarState, CS_prev: car.CarState, CC: car.CarControl):
    if self.CP.brand in ('body', 'mock'):
      return Events()

    events = self.create_common_events(CS, CS_prev)

    if self.CP.brand == 'chrysler':
      # Low speed steer alert hysteresis logic
      if self.CP.minSteerSpeed > 0. and CS.vEgo < (self.CP.minSteerSpeed + 0.5):
        self.low_speed_alert = True
      elif CS.vEgo > (self.CP.minSteerSpeed + 1.):
        self.low_speed_alert = False
      if self.low_speed_alert:
        events.add(EventName.belowSteerSpeed)

    elif self.CP.brand == 'honda':
      if self.CP.pcmCruise and CS.vEgo < self.CP.minEnableSpeed:
        events.add(EventName.belowEngageSpeed)

      if self.CP.pcmCruise:
        # we engage when pcm is active (rising edge)
        if CS.cruiseState.enabled and not CS_prev.cruiseState.enabled:
          events.add(EventName.pcmEnable)
        elif not CS.cruiseState.enabled and (CC.actuators.accel >= 0. or not self.CP.openpilotLongitudinalControl):
          # it can happen that car cruise disables while comma system is enabled: need to
          # keep braking if needed or if the speed is very low
          if CS.vEgo < self.CP.minEnableSpeed + 2.:
            # non loud alert if cruise disables below 25mph as expected (+ a little margin)
            events.add(EventName.speedTooLow)
          else:
            events.add(EventName.cruiseDisabled)
      if self.CP.minEnableSpeed > 0 and CS.vEgo < 0.001:
        events.add(EventName.manualRestart)

    elif self.CP.brand == 'toyota':
      # TODO: when we check for unexpected disengagement, check gear not S1, S2, S3
      if self.CP.openpilotLongitudinalControl:
        # Only can leave standstill when planner wants to move
        if CS.cruiseState.standstill and not CS.brakePressed and (CC.cruiseControl.resume or self.CP.flags & ToyotaFlags.HYBRID.value):
          events.add(EventName.resumeRequired)
        if CS.vEgo < self.CP.minEnableSpeed:
          events.add(EventName.belowEngageSpeed)
          if CC.actuators.accel > 0.3:
            # some margin on the actuator to not false trigger cancellation while stopping
            events.add(EventName.speedTooLow)
          if CS.vEgo < 0.001:
            # while in standstill, send a user alert
            events.add(EventName.manualRestart)

    elif self.CP.brand == 'gm':
      # Enabling at a standstill with brake is allowed
      # TODO: verify 17 Volt can enable for the first time at a stop and allow for all GMs
      if CS.vEgo < self.CP.minEnableSpeed and not (CS.standstill and CS.brake >= 20 and
                                                   self.CP.networkLocation == NetworkLocation.fwdCamera):
        events.add(EventName.belowEngageSpeed)
      if CS.cruiseState.standstill:
        events.add(EventName.resumeRequired)

    elif self.CP.brand == 'volkswagen':
      if self.CP.openpilotLongitudinalControl:
        if CS.vEgo < self.CP.minEnableSpeed + 0.5:
          events.add(EventName.belowEngageSpeed)
        if CC.enabled and CS.vEgo < self.CP.minEnableSpeed:
          events.add(EventName.speedTooLow)

      # TODO: this needs to be implemented generically in carState struct
      # if CC.eps_timer_soft_disable_alert:
      #   events.add(EventName.steerTimeLimit)

    return events