def get_accel(self, v_ego: float, long_active: bool, standstill: bool, cruise_standstill: bool) -> float:
    ready = abs(v_ego - self.initial_speed) < 0.3 and long_active and not cruise_standstill
    if self.initial_speed < 0.01:
      ready = ready and standstill
    self._ready_cnt = (self._ready_cnt + 1) if ready else 0

    if self._ready_cnt > (3. / DT_MDL):
      self._active = True

    if not self._active:
      return min(max(self.initial_speed - v_ego, -2.), 2.)

    return self._step()