def refresh(self) -> int:
    """Refresh alerts from params and return active count."""
    active_count = 0

    # Handle UpdateAvailable alert specially
    update_available = self.params.get_bool("UpdateAvailable")
    update_alert_data = next((alert_data for alert_data in self.sorted_alerts if alert_data.key == "UpdateAvailable"), None)

    if update_alert_data:
      if update_available:
        version_string = ""

        # Get new version description and parse version and date
        new_desc = self.params.get("UpdaterNewDescription") or ""
        if new_desc:
          # format: "version / branch / commit / date"
          parts = new_desc.split(" / ")
          if len(parts) > 3:
            version, date = parts[0], parts[3]
            version_string = f"\nopenpilot {version}, {date}\n"

        update_alert_data.text = f"Update available {version_string}. Click to update. Read the release notes at blog.comma.ai."
        update_alert_data.visible = True
        active_count += 1
      else:
        update_alert_data.text = ""
        update_alert_data.visible = False

    # Handle regular alerts
    for alert_data in self.sorted_alerts:
      if alert_data.key == "UpdateAvailable":
        continue  # Skip, already handled above

      text = ""
      alert_json = self.params.get(alert_data.key)

      if alert_json:
        text = alert_json.get("text", "").replace("%1", alert_json.get("extra", ""))

      alert_data.text = text
      alert_data.visible = bool(text)

      if alert_data.visible:
        active_count += 1

    # Update alert items (they reference the same alert_data objects)
    for alert_item in self.alert_items:
      alert_item.update_alert_data(alert_item.alert_data)

    return active_count