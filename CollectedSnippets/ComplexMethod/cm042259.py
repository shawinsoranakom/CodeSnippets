def _update_events(self, driver_engaged, op_engaged, standstill, wrong_gear):
    self.alert_level = AlertLevel.none
    self.driver_interacting = driver_engaged

    if self.terminal_alert_cnt >= self.settings._MAX_TERMINAL_ALERTS or \
       self.terminal_time >= self.settings._MAX_TERMINAL_DURATION:
      self.too_distracted = True

    always_on_valid = self.always_on and not wrong_gear
    if (self.driver_interacting and self.awareness > 0 and self.active_policy == MonitoringPolicy.wheeltouch) or \
       (not always_on_valid and not op_engaged) or \
       (always_on_valid and not op_engaged and self.awareness <= 0):
      # always reset on disengage with normal mode; disengage resets only on red if always on
      self._reset_awareness()
      return

    awareness_prev = self.awareness
    _reaching_alert_1 = self.awareness - self.step_change <= self.threshold_alert_1
    _reaching_alert_3 = self.awareness - self.step_change <= 0
    standstill_exemption = standstill and _reaching_alert_1
    always_on_exemption = always_on_valid and not op_engaged and _reaching_alert_3

    if self.awareness > 0 and \
       ((self.driver_distraction_filter.x < 0.37 and self.face_detected and self.pose.low_std) or standstill_exemption):
      if self.driver_interacting:
        self._reset_awareness()
        return
      # only restore awareness when paying attention and alert is not red
      self.awareness = min(self.awareness + ((self.settings._TIMEOUT_RECOVERY_FACTOR_MAX-self.settings._TIMEOUT_RECOVERY_FACTOR_MIN)*
                                             (1.-self.awareness)+self.settings._TIMEOUT_RECOVERY_FACTOR_MIN)*self.step_change, 1.)
      if self.awareness == 1.:
        self.last_wheeltouch_awareness = min(self.last_wheeltouch_awareness + self.step_change, 1.)
      # don't display alert banner when awareness is recovering and has cleared orange
      if self.awareness > self.threshold_alert_2:
        return

    certainly_distracted = self.driver_distraction_filter.x > 0.63 and self.driver_distracted and self.face_detected
    maybe_distracted = self.is_model_uncertain or not self.face_detected

    if certainly_distracted or maybe_distracted:
      # should always be counting if distracted unless at standstill and reaching green
      # also will not be reaching 0 if DM is active when not engaged
      if not (standstill_exemption or always_on_exemption):
        self.awareness = max(self.awareness - self.step_change, -0.1)

    if self.awareness <= 0.:
      # terminal alert: disengagement required
      self.alert_level = AlertLevel.three
      self.terminal_time += 1
      if awareness_prev > 0.:
        self.terminal_alert_cnt += 1
    elif self.awareness <= self.threshold_alert_2:
      self.alert_level = AlertLevel.two
    elif self.awareness <= self.threshold_alert_1:
      self.alert_level = AlertLevel.one