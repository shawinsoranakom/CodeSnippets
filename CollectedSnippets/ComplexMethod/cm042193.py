def handle_log(self, t, which, msg):
    if which == "carControl":
      self.raw_points["carControl_t"].append(t + self.lag)
      self.raw_points["lat_active"].append(msg.latActive)
    elif which == "carOutput":
      self.raw_points["carOutput_t"].append(t + self.lag)
      self.raw_points["steer_torque"].append(-msg.actuatorsOutput.torque)
    elif which == "carState":
      self.raw_points["carState_t"].append(t + self.lag)
      # TODO: check if high aEgo affects resulting lateral accel
      self.raw_points["vego"].append(msg.vEgo)
      self.raw_points["steer_override"].append(msg.steeringPressed)
    elif which == "liveCalibration":
      self.calibrator.feed_live_calib(msg)
    elif which == "liveDelay":
      self.lag = msg.lateralDelay
    # calculate lateral accel from past steering torque
    elif which == "livePose":
      is_valid = msg.angularVelocityDevice.valid and msg.orientationNED.valid and msg.inputsOK and msg.sensorsOK and msg.posenetOK
      if len(self.raw_points['steer_torque']) == self.hist_len and is_valid:
        t = msg.timestamp * 1e-9
        device_pose = Pose.from_live_pose(msg)
        calibrated_pose = self.calibrator.build_calibrated_pose(device_pose)
        angular_velocity_calibrated = calibrated_pose.angular_velocity

        yaw_rate = angular_velocity_calibrated.yaw
        roll = device_pose.orientation.roll
        # check lat active up to now (without lag compensation)
        lat_active = np.interp(np.arange(t - MIN_ENGAGE_BUFFER, t + self.lag, DT_MDL),
                               self.raw_points['carControl_t'], self.raw_points['lat_active']).astype(bool)
        steer_override = np.interp(np.arange(t - MIN_ENGAGE_BUFFER, t + self.lag, DT_MDL),
                                   self.raw_points['carState_t'], self.raw_points['steer_override']).astype(bool)
        vego = np.interp(t, self.raw_points['carState_t'], self.raw_points['vego'])
        steer = np.interp(t, self.raw_points['carOutput_t'], self.raw_points['steer_torque']).item()
        lateral_acc = (vego * yaw_rate) - (np.sin(roll) * ACCELERATION_DUE_TO_GRAVITY).item()
        if all(lat_active) and not any(steer_override) and (vego > MIN_VEL) and (abs(steer) > STEER_MIN_THRESHOLD):
          if abs(lateral_acc) <= LAT_ACC_THRESHOLD:
            self.filtered_points.add_point(steer, lateral_acc)

          if self.track_all_points:
            self.all_torque_points.append([steer, lateral_acc])