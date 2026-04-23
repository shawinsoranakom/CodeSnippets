def refresh(self):
    if not self.sorted_alerts:
      self._build_alerts()

    active_count = 0
    connectivity_needed = False
    excessive_actuation = False

    for alert_data in self.sorted_alerts:
      text = ""
      alert_json = self.params.get(alert_data.key)

      if alert_json:
        text = alert_json.get("text", "").replace("%1", alert_json.get("extra", ""))

      alert_data.text = text
      alert_data.visible = bool(text)

      if alert_data.visible:
        active_count += 1

      if alert_data.key == "Offroad_ConnectivityNeeded" and alert_data.visible:
        connectivity_needed = True

      if alert_data.key == "Offroad_ExcessiveActuation" and alert_data.visible:
        excessive_actuation = True

    self.excessive_actuation_btn.set_visible(excessive_actuation)
    self.snooze_btn.set_visible(connectivity_needed and not excessive_actuation)
    return active_count