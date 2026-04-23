def reset(self, rpy_init: np.ndarray = RPY_INIT,
                  valid_blocks: int = 0,
                  wide_from_device_euler_init: np.ndarray = WIDE_FROM_DEVICE_EULER_INIT,
                  height_init: np.ndarray = HEIGHT_INIT,
                  smooth_from: np.ndarray | None = None) -> None:
    if not np.isfinite(rpy_init).all():
      self.rpy = RPY_INIT.copy()
    else:
      self.rpy = rpy_init.copy()

    if not np.isfinite(height_init).all() or len(height_init) != 1:
      self.height = HEIGHT_INIT.copy()
    else:
      self.height = height_init.copy()

    if not np.isfinite(wide_from_device_euler_init).all() or len(wide_from_device_euler_init) != 3:
      self.wide_from_device_euler = WIDE_FROM_DEVICE_EULER_INIT.copy()
    else:
      self.wide_from_device_euler = wide_from_device_euler_init.copy()

    if not np.isfinite(valid_blocks) or valid_blocks < 0:
      self.valid_blocks = 0
    else:
      self.valid_blocks = valid_blocks

    self.rpys = np.tile(self.rpy, (INPUTS_WANTED, 1))
    self.wide_from_device_eulers = np.tile(self.wide_from_device_euler, (INPUTS_WANTED, 1))
    self.heights = np.tile(self.height, (INPUTS_WANTED, 1))

    self.idx = 0
    self.block_idx = 0
    self.v_ego = 0.0

    if smooth_from is None:
      self.old_rpy = RPY_INIT
      self.old_rpy_weight = 0.0
    else:
      self.old_rpy = smooth_from
      self.old_rpy_weight = 1.0