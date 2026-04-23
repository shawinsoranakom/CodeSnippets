def handle_log(self, t: float, which: str, msg: capnp._DynamicStructReader):
    if which == 'livePose':
      t = msg.timestamp * 1e-9
      device_pose = Pose.from_live_pose(msg)
      calibrated_pose = self.calibrator.build_calibrated_pose(device_pose)

      yaw_rate, yaw_rate_std = calibrated_pose.angular_velocity.z, calibrated_pose.angular_velocity.z_std
      yaw_rate_valid = msg.angularVelocityDevice.valid
      yaw_rate_valid = yaw_rate_valid and 0 < yaw_rate_std < 10  # rad/s
      yaw_rate_valid = yaw_rate_valid and abs(yaw_rate) < 1  # rad/s
      if not yaw_rate_valid:
        # This is done to bound the yaw rate estimate when localizer values are invalid or calibrating
        yaw_rate, yaw_rate_std = 0.0, np.radians(10.0)
      self.observed_yaw_rate = yaw_rate

      localizer_roll, localizer_roll_std = device_pose.orientation.x, device_pose.orientation.x_std
      localizer_roll_std = np.radians(1) if np.isnan(localizer_roll_std) else localizer_roll_std
      roll_valid = (localizer_roll_std < ROLL_STD_MAX) and (ROLL_MIN < localizer_roll < ROLL_MAX) and msg.sensorsOK
      if roll_valid:
        roll = localizer_roll
        # Experimentally found multiplier of 2 to be best trade-off between stability and accuracy or similar?
        roll_std = 2 * localizer_roll_std
      else:
        # This is done to bound the road roll estimate when localizer values are invalid
        roll = 0.0
        roll_std = np.radians(10.0)
      self.observed_roll = np.clip(roll, self.observed_roll - ROLL_MAX_DELTA, self.observed_roll + ROLL_MAX_DELTA)

      if self.active:
        if msg.posenetOK:
          self.kf.predict_and_observe(t,
                                      ObservationKind.ROAD_FRAME_YAW_RATE,
                                      np.array([[-self.observed_yaw_rate]]),
                                      np.array([np.atleast_2d(yaw_rate_std**2)]))

          self.kf.predict_and_observe(t,
                                      ObservationKind.ROAD_ROLL,
                                      np.array([[self.observed_roll]]),
                                      np.array([np.atleast_2d(roll_std**2)]))
        self.kf.predict_and_observe(t, ObservationKind.ANGLE_OFFSET_FAST, np.array([[0]]))

        # We observe the current stiffness and steer ratio (with a high observation noise) to bound
        # the respective estimate STD. Otherwise the STDs keep increasing, causing rapid changes in the
        # states in longer routes (especially straight stretches).
        stiffness = float(self.kf.x[States.STIFFNESS].item())
        steer_ratio = float(self.kf.x[States.STEER_RATIO].item())
        self.kf.predict_and_observe(t, ObservationKind.STIFFNESS, np.array([[stiffness]]))
        self.kf.predict_and_observe(t, ObservationKind.STEER_RATIO, np.array([[steer_ratio]]))

    elif which == 'liveCalibration':
      self.calibrator.feed_live_calib(msg)

    elif which == 'carState':
      steering_angle = msg.steeringAngleDeg

      in_linear_region = abs(steering_angle) < 45
      self.observed_speed = msg.vEgo
      self.active = self.observed_speed > MIN_ACTIVE_SPEED and in_linear_region

      if self.active:
        self.kf.predict_and_observe(t, ObservationKind.STEER_ANGLE, np.array([[np.radians(steering_angle)]]))
        self.kf.predict_and_observe(t, ObservationKind.ROAD_FRAME_X_SPEED, np.array([[self.observed_speed]]))

    if not self.active:
      # Reset time when stopped so uncertainty doesn't grow
      self.kf.filter.set_filter_time(t)
      self.kf.filter.reset_rewind()