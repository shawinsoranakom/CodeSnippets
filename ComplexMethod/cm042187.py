def handle_log(self, t: float, which: str, msg: capnp._DynamicStructReader):
    if which == "carControl":
      self.lat_active = msg.latActive
    elif which == "carState":
      self.steering_pressed = msg.steeringPressed
      self.v_ego = msg.vEgo
    elif which == "controlsState":
      self.steering_saturated = getattr(msg.lateralControlState, msg.lateralControlState.which()).saturated
      self.desired_curvature = msg.desiredCurvature
    elif which == "liveCalibration":
      self.calibrator.feed_live_calib(msg)
    elif which == "livePose":
      device_pose = Pose.from_live_pose(msg)
      calibrated_pose = self.calibrator.build_calibrated_pose(device_pose)
      self.yaw_rate = calibrated_pose.angular_velocity.yaw
      self.yaw_rate_std = calibrated_pose.angular_velocity.yaw_std
      self.pose_valid = msg.angularVelocityDevice.valid and msg.posenetOK and msg.inputsOK
    self.t = t