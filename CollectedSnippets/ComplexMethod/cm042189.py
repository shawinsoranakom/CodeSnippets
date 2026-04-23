def update_estimate(self):
    if not self.points_enough():
      return

    times, desired, actual, okay = self.points.get()
    # check if there are any new valid data points since the last update
    is_valid = self.points_valid() and (actual.max() - actual.min() >= MIN_LAT_ACCEL_RANGE)
    if self.last_estimate_t != 0 and times[0] <= self.last_estimate_t:
      new_values_start_idx = next(-i for i, t in enumerate(reversed(times)) if t <= self.last_estimate_t)
      is_valid = is_valid and not (new_values_start_idx == 0 or not np.any(okay[new_values_start_idx:]))

    desired = masked_symmetric_moving_average(desired, okay, SMOOTH_K, SMOOTH_SIGMA)
    actual = masked_symmetric_moving_average(actual, okay, SMOOTH_K, SMOOTH_SIGMA)

    delay, corr, confidence = self.actuator_delay(desired, actual, okay, self.dt, MIN_LAG, MAX_LAG)
    if corr < self.min_ncc or confidence < self.min_confidence or not is_valid:
      return

    self.block_avg.update(delay)
    self.last_estimate_t = self.t