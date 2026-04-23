def _set_policy(self, target_policy):
    if self.active_policy == MonitoringPolicy.vision and self.awareness <= self.threshold_alert_2:
      if target_policy == MonitoringPolicy.vision:
        self.step_change = DT_DMON / self.settings._VISION_POLICY_ALERT_3_TIMEOUT
      else:
        self.step_change = 0.
      return  # no exploit after orange alert
    elif self.awareness <= 0.:
      return

    if target_policy == MonitoringPolicy.vision:
      # when falling back from passive mode to active mode, reset awareness to avoid false alert
      if self.active_policy != MonitoringPolicy.vision:
        self.last_wheeltouch_awareness = self.awareness
        self.awareness = self.last_vision_awareness

      self.threshold_alert_1 = 1. - self.settings._VISION_POLICY_ALERT_1_TIMEOUT / self.settings._VISION_POLICY_ALERT_3_TIMEOUT
      self.threshold_alert_2 = 1. - self.settings._VISION_POLICY_ALERT_2_TIMEOUT / self.settings._VISION_POLICY_ALERT_3_TIMEOUT
      self.step_change = DT_DMON / self.settings._VISION_POLICY_ALERT_3_TIMEOUT
      self.active_policy = MonitoringPolicy.vision
    else:
      if self.active_policy == MonitoringPolicy.vision:
        self.last_vision_awareness = self.awareness
        self.awareness = self.last_wheeltouch_awareness

      self.threshold_alert_1 = 1. - self.settings._WHEELTOUCH_POLICY_ALERT_1_TIMEOUT / self.settings._WHEELTOUCH_POLICY_ALERT_3_TIMEOUT
      self.threshold_alert_2 = 1. - self.settings._WHEELTOUCH_POLICY_ALERT_2_TIMEOUT / self.settings._WHEELTOUCH_POLICY_ALERT_3_TIMEOUT
      self.step_change = DT_DMON / self.settings._WHEELTOUCH_POLICY_ALERT_3_TIMEOUT
      self.active_policy = MonitoringPolicy.wheeltouch