def process_alerts(self, frame: int, clear_event_types: set):
    ae = AlertEntry()
    for v in self.alerts.values():
      if not v.alert:
        continue

      if v.alert.event_type in clear_event_types:
        v.end_frame = -1

      # sort by priority first and then by start_frame
      greater = ae.alert is None or (v.alert.priority, v.start_frame) > (ae.alert.priority, ae.start_frame)
      if v.active(frame) and greater:
        ae = v

    self.current_alert = ae.alert if ae.alert is not None else EmptyAlert