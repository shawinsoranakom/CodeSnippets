def handle_log(self, t: float, which: str, msg: capnp._DynamicStructReader) -> HandleLogResult:
    new_x, new_P = None, None
    if which == "accelerometer" and msg.which() == "acceleration":
      sensor_time = msg.timestamp * 1e-9

      if not self._validate_sensor_time(sensor_time, t) or not self._validate_timestamp(sensor_time):
        return HandleLogResult.TIMING_INVALID

      if not self._validate_sensor_source(msg.source):
        return HandleLogResult.SENSOR_SOURCE_INVALID

      v = msg.acceleration.v
      meas = np.array([-v[2], -v[1], -v[0]])
      if np.linalg.norm(meas) >= ACCEL_SANITY_CHECK:
        return HandleLogResult.INPUT_INVALID

      acc_res = self.kf.predict_and_observe(sensor_time, ObservationKind.PHONE_ACCEL, meas)
      if acc_res is not None:
        _, new_x, _, new_P, _, _, (acc_err,), _, _ = acc_res
        self.observation_errors[ObservationKind.PHONE_ACCEL] = np.array(acc_err)
        self.observations[ObservationKind.PHONE_ACCEL] = meas

    elif which == "gyroscope" and msg.which() == "gyroUncalibrated":
      sensor_time = msg.timestamp * 1e-9

      if not self._validate_sensor_time(sensor_time, t) or not self._validate_timestamp(sensor_time):
        return HandleLogResult.TIMING_INVALID

      if not self._validate_sensor_source(msg.source):
        return HandleLogResult.SENSOR_SOURCE_INVALID

      v = msg.gyroUncalibrated.v
      meas = np.array([-v[2], -v[1], -v[0]])

      gyro_bias = self.kf.x[States.GYRO_BIAS]
      gyro_camodo_yawrate_err = np.abs((meas[2] - gyro_bias[2]) - self.camodo_yawrate_distribution[0])
      gyro_camodo_yawrate_err_threshold = YAWRATE_CROSS_ERR_CHECK_FACTOR * self.camodo_yawrate_distribution[1]
      gyro_valid = gyro_camodo_yawrate_err < gyro_camodo_yawrate_err_threshold

      if np.linalg.norm(meas) >= ROTATION_SANITY_CHECK or not gyro_valid:
        return HandleLogResult.INPUT_INVALID

      gyro_res = self.kf.predict_and_observe(sensor_time, ObservationKind.PHONE_GYRO, meas)
      if gyro_res is not None:
        _, new_x, _, new_P, _, _, (gyro_err,), _, _ = gyro_res
        self.observation_errors[ObservationKind.PHONE_GYRO] = np.array(gyro_err)
        self.observations[ObservationKind.PHONE_GYRO] = meas

    elif which == "carState":
      self.car_speed = abs(msg.vEgo)

    elif which == "liveCalibration":
      # Note that we use this message during calibration
      if len(msg.rpyCalib) > 0:
        calib = np.array(msg.rpyCalib)
        if calib.min() < -CALIB_RPY_SANITY_CHECK or calib.max() > CALIB_RPY_SANITY_CHECK:
          return HandleLogResult.INPUT_INVALID

        self.device_from_calib = rot_from_euler(calib)

    elif which == "cameraOdometry":
      # camera odometry is delayed depending on the model context frames and temporal frequency
      t = msg.timestampEof * 1e-9 - CAM_ODO_POSE_DELAY
      if not self._validate_timestamp(t):
        return HandleLogResult.TIMING_INVALID

      rot_device = np.matmul(self.device_from_calib, np.array(msg.rot))
      trans_device = np.matmul(self.device_from_calib, np.array(msg.trans))

      if np.linalg.norm(rot_device) > ROTATION_SANITY_CHECK or np.linalg.norm(trans_device) > TRANS_SANITY_CHECK:
        return HandleLogResult.INPUT_INVALID

      rot_calib_std = np.array(msg.rotStd)
      trans_calib_std = np.array(msg.transStd)

      if rot_calib_std.min() <= MIN_STD_SANITY_CHECK or trans_calib_std.min() <= MIN_STD_SANITY_CHECK:
        return HandleLogResult.INPUT_INVALID

      if np.linalg.norm(rot_calib_std) > 10 * ROTATION_SANITY_CHECK or np.linalg.norm(trans_calib_std) > 10 * TRANS_SANITY_CHECK:
        return HandleLogResult.INPUT_INVALID

      self.posenet_stds = np.roll(self.posenet_stds, -1)
      self.posenet_stds[-1] = trans_calib_std[0]

      # Multiply by N to avoid to high certainty in kalman filter because of temporally correlated noise
      rot_calib_std *= CAM_ODO_ROT_STD_MULT
      trans_calib_std *= CAM_ODO_TRANS_STD_MULT

      rot_device_std = rotate_std(self.device_from_calib, rot_calib_std)
      trans_device_std = rotate_std(self.device_from_calib, trans_calib_std)
      rot_device_noise = rot_device_std ** 2
      trans_device_noise = trans_device_std ** 2

      cam_odo_rot_res = self.kf.predict_and_observe(t, ObservationKind.CAMERA_ODO_ROTATION, rot_device, np.array([np.diag(rot_device_noise)]))
      cam_odo_trans_res = self.kf.predict_and_observe(t, ObservationKind.CAMERA_ODO_TRANSLATION, trans_device, np.array([np.diag(trans_device_noise)]))
      self.camodo_yawrate_distribution =  np.array([rot_device[2], rot_device_std[2]])
      if cam_odo_rot_res is not None:
        _, new_x, _, new_P, _, _, (cam_odo_rot_err,), _, _ = cam_odo_rot_res
        self.observation_errors[ObservationKind.CAMERA_ODO_ROTATION] = np.array(cam_odo_rot_err)
        self.observations[ObservationKind.CAMERA_ODO_ROTATION] = rot_device
      if cam_odo_trans_res is not None:
        _, new_x, _, new_P, _, _, (cam_odo_trans_err,), _, _ = cam_odo_trans_res
        self.observation_errors[ObservationKind.CAMERA_ODO_TRANSLATION] = np.array(cam_odo_trans_err)
        self.observations[ObservationKind.CAMERA_ODO_TRANSLATION] = trans_device

    if new_x is not None and new_P is not None:
      self._finite_check(t, new_x, new_P)
    return HandleLogResult.SUCCESS