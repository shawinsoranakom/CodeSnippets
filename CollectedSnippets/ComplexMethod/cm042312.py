def _update_state(self):
    super()._update_state()

    if ui_state.started:
      self.set_enabled(False)
      return

    updater_state = ui_state.params.get("UpdaterState") or ""
    failed_count = ui_state.params.get("UpdateFailedCount")
    failed = False if failed_count is None else int(failed_count) > 0

    if ui_state.params.get_bool("UpdateAvailable"):
      self.set_rotate_icon(False)
      self.set_enabled(True)
      if self.get_value() != "update now":
        self.set_value("update now")
        self.set_icon(self._txt_reboot_icon)

    elif self._state == UpdaterState.WAITING_FOR_UPDATER:
      self.set_rotate_icon(True)
      if updater_state != "idle":
        self._state = UpdaterState.UPDATER_RESPONDING

      # Recover from updater not responding (time invalid shortly after boot)
      if self._waiting_for_updater_t is None:
        self._waiting_for_updater_t = rl.get_time()

      if self._waiting_for_updater_t is not None and rl.get_time() - self._waiting_for_updater_t > UPDATER_TIMEOUT:
        self.set_rotate_icon(False)
        self.set_value("updater failed\nto respond")
        self._state = UpdaterState.IDLE
        self._hide_value_t = rl.get_time()

    elif self._state == UpdaterState.UPDATER_RESPONDING:
      if updater_state == "idle":
        self.set_rotate_icon(False)
        self._state = UpdaterState.IDLE
        self._hide_value_t = rl.get_time()
      else:
        if self.get_value() != updater_state:
          self.set_value(updater_state)

    elif self._state == UpdaterState.IDLE:
      self.set_rotate_icon(False)
      if failed:
        if self.get_value() != "failed to update":
          self.set_value("failed to update")

      elif ui_state.params.get_bool("UpdaterFetchAvailable"):
        self.set_enabled(True)
        if self.get_value() != "download update":
          self.set_value("download update")

      elif self._hide_value_t is not None:
        self.set_enabled(True)
        if self.get_value() == "checking...":
          self.set_value("up to date")
          self.set_icon(self._txt_up_to_date_icon)

        # Hide previous text after short amount of time (up to date or failed)
        if rl.get_time() - self._hide_value_t > 3.0:
          self._hide_value_t = None
          self.set_value("")
          self.set_icon(self._txt_update_icon)
      else:
        if self.get_value() != "":
          self.set_value("")

    if self._state != UpdaterState.WAITING_FOR_UPDATER:
      self._waiting_for_updater_t = None