def _update_states(self, driver_state, cal_rpy, car_speed, op_engaged, standstill, demo_mode=False, steering_angle_deg=0.):
    rhd_pred = driver_state.wheelOnRightProb
    # calibrates only when there's movement and either face detected
    if car_speed > self.settings._WHEELPOS_CALIB_MIN_SPEED and (driver_state.leftDriverData.faceProb > self.settings._FACE_THRESHOLD or
                                          driver_state.rightDriverData.faceProb > self.settings._FACE_THRESHOLD):
      self.wheelpos_offsetter.push_and_update(rhd_pred)

    wheelpos_calibrated = self.wheelpos_offsetter.filtered_stat.n >= self.settings._WHEELPOS_FILTER_MIN_COUNT

    if wheelpos_calibrated or demo_mode:
      self.wheel_on_right = self.wheelpos_offsetter.filtered_stat.M > self.settings._WHEELPOS_THRESHOLD
    else:
      self.wheel_on_right = self.wheel_on_right_default # use default/saved if calibration is unfinished
    # make sure no switching when engaged
    if op_engaged and self.wheel_on_right_last is not None and self.wheel_on_right_last != self.wheel_on_right and not demo_mode:
      self.wheel_on_right = self.wheel_on_right_last
    driver_data = driver_state.rightDriverData if self.wheel_on_right else driver_state.leftDriverData
    if not all(len(x) > 0 for x in (driver_data.faceOrientation, driver_data.facePosition,
                                    driver_data.faceOrientationStd, driver_data.facePositionStd)):
      return

    self.face_detected = driver_data.faceProb > self.settings._FACE_THRESHOLD
    self.pose.pitch, self.pose.yaw = face_orientation_from_model(driver_data.faceOrientation, driver_data.facePosition, cal_rpy)
    steer_d = max(abs(steering_angle_deg) - self.settings._POSE_YAW_MIN_STEER_DEG, 0.)
    self.pose.steer_yaw_offset = radians(steer_d) * -np.sign(steering_angle_deg) * self.settings._POSE_YAW_STEER_FACTOR
    if self.wheel_on_right:
      self.pose.yaw *= -1
      self.pose.steer_yaw_offset *= -1
    self.wheel_on_right_last = self.wheel_on_right
    self.model_std_max = max(driver_data.faceOrientationStd[0], driver_data.faceOrientationStd[1])
    self.pose.low_std = self.model_std_max < self.settings._HI_STD_THRESHOLD
    self.blink_prob = driver_data.eyesClosedProb * (driver_data.eyesVisibleProb > self.settings._EYE_THRESHOLD)
    self.phone_prob = driver_data.phoneProb

    self._get_distracted_types()
    self.driver_distracted = any(self.distracted_types.values()) and driver_data.faceProb > self.settings._FACE_THRESHOLD and self.pose.low_std
    self.driver_distraction_filter.update(self.driver_distracted)

    # only update offsetter when driver is actively driving the car above a certain speed
    if self.face_detected and car_speed > self.settings._POSE_CALIB_MIN_SPEED and self.pose.low_std and (not op_engaged or not self.driver_distracted):
      self.pose.pitch_offsetter.push_and_update(self.pose.pitch)
      self.pose.yaw_offsetter.push_and_update(self.pose.yaw)

    self.pose.calibrated = self.pose.pitch_offsetter.filtered_stat.n >= self.settings._POSE_OFFSET_MIN_COUNT and \
                           self.pose.yaw_offsetter.filtered_stat.n >= self.settings._POSE_OFFSET_MIN_COUNT

    if self.face_detected and not self.driver_distracted:
      dcam_uncertain = self.model_std_max > self.settings._DCAM_UNCERTAIN_ALERT_THRESHOLD
      if dcam_uncertain and not standstill:
        self.dcam_uncertain_cnt += 1
        self.dcam_reset_cnt = 0
      else:
        self.dcam_reset_cnt += 1
        if self.dcam_reset_cnt > self.settings._DCAM_UNCERTAIN_RESET_COUNT:
          self.dcam_uncertain_cnt = 0

    self.is_model_uncertain = self.hi_stds >= self.settings._HI_STD_FALLBACK_TIME
    self._set_policy(MonitoringPolicy.vision if self.face_detected and not self.is_model_uncertain else MonitoringPolicy.wheeltouch)
    if self.face_detected and not self.pose.low_std and not self.driver_distracted:
      self.hi_stds += 1
    elif self.face_detected and self.pose.low_std:
      self.hi_stds = 0