def update_status(self) -> None:
    valid_idxs = self.get_valid_idxs()
    if valid_idxs:
      self.wide_from_device_euler = np.mean(self.wide_from_device_eulers[valid_idxs], axis=0)
      self.height = np.mean(self.heights[valid_idxs], axis=0)
      rpys = self.rpys[valid_idxs]
      self.rpy = np.mean(rpys, axis=0)
      max_rpy_calib = np.array(np.max(rpys, axis=0))
      min_rpy_calib = np.array(np.min(rpys, axis=0))
      self.calib_spread = np.abs(max_rpy_calib - min_rpy_calib)
    else:
      self.calib_spread = np.zeros(3)

    if self.valid_blocks < INPUTS_NEEDED:
      if self.cal_status == log.LiveCalibrationData.Status.recalibrating:
        self.cal_status = log.LiveCalibrationData.Status.recalibrating
      else:
        self.cal_status = log.LiveCalibrationData.Status.uncalibrated
    elif is_calibration_valid(self.rpy):
      self.cal_status = log.LiveCalibrationData.Status.calibrated
    else:
      self.cal_status = log.LiveCalibrationData.Status.invalid

    # If spread is too high, assume mounting was changed and reset to last block.
    # Make the transition smooth. Abrupt transitions are not good for feedback loop through supercombo model.
    # TODO: add height spread check with smooth transition too
    spread_too_high = self.calib_spread[1] > MAX_ALLOWED_PITCH_SPREAD or self.calib_spread[2] > MAX_ALLOWED_YAW_SPREAD
    if spread_too_high and self.cal_status == log.LiveCalibrationData.Status.calibrated:
      self.reset(self.rpys[self.block_idx - 1], valid_blocks=1, smooth_from=self.rpy)
      self.cal_status = log.LiveCalibrationData.Status.recalibrating

    write_this_cycle = (self.idx == 0) and (self.block_idx % (INPUTS_WANTED//5) == 5)
    if self.param_put and write_this_cycle:
      self.params.put_nonblocking("CalibrationParams", self.get_msg(True).to_bytes())