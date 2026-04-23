def _update_state(self):
    super()._update_state()
    if device.awake and not ui_state.params.get_bool("IsDriverViewEnabled"):
      ui_state.params.put_bool_nonblocking("IsDriverViewEnabled", True)

    sm = ui_state.sm
    if sm.recv_frame.get("driverMonitoringState", 0) == 0:
      return

    dm_state = sm["driverMonitoringState"]
    driver_data = self._dialog.driver_state_renderer.get_driver_data()

    if len(driver_data.faceOrientation) == 3:
      pitch, yaw, _ = driver_data.faceOrientation
      looking_center = abs(math.degrees(pitch)) < self.LOOKING_THRESHOLD_DEG and abs(math.degrees(yaw)) < self.LOOKING_THRESHOLD_DEG
    else:
      looking_center = False

    # stay at 100% once reached
    in_bad_face = gui_app.get_active_widget() == self._bad_face_page
    if ((dm_state.visionPolicyState.faceDetected and looking_center) or self._progress.x > 0.99) and not in_bad_face:
      slow = self._progress.x < 0.25
      duration = self.PROGRESS_DURATION * 2 if slow else self.PROGRESS_DURATION
      self._progress.x += 1.0 / (duration * gui_app.target_fps)
      self._progress.x = min(1.0, self._progress.x)
    else:
      self._progress.update(0.0)

    self._good_button.set_enabled(self._progress.x >= 0.999)