def handle_cam_odom(self, trans: list[float],
                            rot: list[float],
                            wide_from_device_euler: list[float],
                            trans_std: list[float],
                            road_transform_trans: list[float],
                            road_transform_trans_std: list[float]) -> np.ndarray | None:
    self.old_rpy_weight = max(0.0, self.old_rpy_weight - 1/SMOOTH_CYCLES)

    straight_and_fast = ((self.v_ego > MIN_SPEED_FILTER) and (trans[0] > MIN_SPEED_FILTER) and (abs(rot[2]) < MAX_YAW_RATE_FILTER))
    angle_std_threshold = MAX_VEL_ANGLE_STD
    height_std_threshold = MAX_HEIGHT_STD
    rpy_certain = np.arctan2(trans_std[1], trans[0]) < angle_std_threshold
    if len(road_transform_trans_std) == 3:
      height_certain = road_transform_trans_std[2] < height_std_threshold
    else:
      height_certain = True

    certain_if_calib = (rpy_certain and height_certain) or (self.valid_blocks < INPUTS_NEEDED)
    if not (straight_and_fast and certain_if_calib):
      return None

    observed_rpy = np.array([0,
                             -np.arctan2(trans[2], trans[0]),
                             np.arctan2(trans[1], trans[0])])
    new_rpy = euler_from_rot(rot_from_euler(self.get_smooth_rpy()).dot(rot_from_euler(observed_rpy)))
    new_rpy = sanity_clip(new_rpy)

    if len(wide_from_device_euler) == 3:
      new_wide_from_device_euler = np.array(wide_from_device_euler)
    else:
      new_wide_from_device_euler = WIDE_FROM_DEVICE_EULER_INIT

    if (len(road_transform_trans) == 3):
      new_height = np.array([road_transform_trans[2]])
    else:
      new_height = HEIGHT_INIT

    self.rpys[self.block_idx] = moving_avg_with_linear_decay(self.rpys[self.block_idx], new_rpy, self.idx, float(BLOCK_SIZE))
    self.wide_from_device_eulers[self.block_idx] = moving_avg_with_linear_decay(self.wide_from_device_eulers[self.block_idx],
                                                                                new_wide_from_device_euler, self.idx, float(BLOCK_SIZE))
    self.heights[self.block_idx] = moving_avg_with_linear_decay(self.heights[self.block_idx], new_height, self.idx, float(BLOCK_SIZE))

    self.idx = (self.idx + 1) % BLOCK_SIZE
    if self.idx == 0:
      self.block_idx += 1
      self.valid_blocks = max(self.block_idx, self.valid_blocks)
      self.block_idx = self.block_idx % INPUTS_WANTED

    self.update_status()

    return new_rpy