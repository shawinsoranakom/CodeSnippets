def _update_calib_description(self):
    desc = tr(DESCRIPTIONS['reset_calibration'])

    calib_bytes = self._params.get("CalibrationParams")
    if calib_bytes:
      try:
        calib = messaging.log_from_bytes(calib_bytes, log.Event).liveCalibration

        if calib.calStatus != log.LiveCalibrationData.Status.uncalibrated:
          pitch = math.degrees(calib.rpyCalib[1])
          yaw = math.degrees(calib.rpyCalib[2])
          desc += tr(" Your device is pointed {:.1f}° {} and {:.1f}° {}.").format(abs(pitch), tr("down") if pitch > 0 else tr("up"),
                                                                                  abs(yaw), tr("left") if yaw > 0 else tr("right"))
      except Exception:
        cloudlog.exception("invalid CalibrationParams")

    lag_perc = 0
    lag_bytes = self._params.get("LiveDelay")
    if lag_bytes:
      try:
        lag_perc = messaging.log_from_bytes(lag_bytes, log.Event).liveDelay.calPerc
      except Exception:
        cloudlog.exception("invalid LiveDelay")
    if lag_perc < 100:
      desc += tr("<br><br>Steering lag calibration is {}% complete.").format(lag_perc)
    else:
      desc += tr("<br><br>Steering lag calibration is complete.")

    torque_bytes = self._params.get("LiveTorqueParameters")
    if torque_bytes:
      try:
        torque = messaging.log_from_bytes(torque_bytes, log.Event).liveTorqueParameters
        # don't add for non-torque cars
        if torque.useParams:
          torque_perc = torque.calPerc
          if torque_perc < 100:
            desc += tr(" Steering torque response calibration is {}% complete.").format(torque_perc)
          else:
            desc += tr(" Steering torque response calibration is complete.")
      except Exception:
        cloudlog.exception("invalid LiveTorqueParameters")

    desc += "<br><br>"
    desc += tr("openpilot is continuously calibrating, resetting is rarely required. " +
               "Resetting calibration will restart openpilot if the car is powered on.")

    self._reset_calib_btn.set_description(desc)