def get_alert(self, sm: messaging.SubMaster) -> Alert | None:
    """Generate the current alert based on selfdrive state."""
    ss = sm['selfdriveState']

    # Check if selfdriveState messages have stopped arriving
    if not sm.updated['selfdriveState']:
      recv_frame = sm.recv_frame['selfdriveState']
      time_since_onroad = time.monotonic() - ui_state.started_time

      # 1. Never received selfdriveState since going onroad
      waiting_for_startup = recv_frame < ui_state.started_frame
      if waiting_for_startup and time_since_onroad > 5:
        return ALERT_STARTUP_PENDING

      # 2. Lost communication with selfdriveState after receiving it
      if TICI and not waiting_for_startup:
        ss_missing = time.monotonic() - sm.recv_time['selfdriveState']
        if ss_missing > SELFDRIVE_STATE_TIMEOUT:
          if ss.enabled and (ss_missing - SELFDRIVE_STATE_TIMEOUT) < SELFDRIVE_UNRESPONSIVE_TIMEOUT:
            return ALERT_CRITICAL_TIMEOUT
          return ALERT_CRITICAL_REBOOT

    # No alert if size is none
    if ss.alertSize == 0:
      return None

    # Return current alert
    ret = Alert(text1=ss.alertText1, text2=ss.alertText2, size=ss.alertSize.raw, status=ss.alertStatus.raw,
                visual_alert=ss.alertHudVisual, alert_type=ss.alertType)
    self._prev_alert = ret
    return ret