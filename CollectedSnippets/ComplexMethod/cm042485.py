def read_sensors(self, state: SimulatorState):
    while self.vehicle_state_recv.poll(0):
      md_vehicle: metadrive_vehicle_state = self.vehicle_state_recv.recv()
      curr_pos = md_vehicle.position

      state.velocity = md_vehicle.velocity
      state.bearing = md_vehicle.bearing
      state.steering_angle = md_vehicle.steering_angle
      state.gps.from_xy(curr_pos)
      state.valid = True

      is_engaged = state.is_engaged
      if is_engaged and self.first_engage is None:
        self.first_engage = time.monotonic()
        self.op_engaged.set()

      # check moving 5 seconds after engaged, doesn't move right away
      after_engaged_check = is_engaged and time.monotonic() - self.first_engage >= 5 and self.test_run

      x_dist = abs(curr_pos[0] - self.vehicle_last_pos[0])
      y_dist = abs(curr_pos[1] - self.vehicle_last_pos[1])
      dist_threshold = 1
      if x_dist >= dist_threshold or y_dist >= dist_threshold: # position not the same during staying still, > threshold is considered moving
        self.distance_moved += x_dist + y_dist

      time_check_threshold = 29
      current_time = time.monotonic()
      since_last_check = current_time - self.last_check_timestamp
      if since_last_check >= time_check_threshold:
        if after_engaged_check and self.distance_moved == 0:
          self.status_q.put(QueueMessage(QueueMessageType.TERMINATION_INFO, {"vehicle_not_moving" : True}))
          self.exit_event.set()

        self.last_check_timestamp = current_time
        self.distance_moved = 0
        self.vehicle_last_pos = curr_pos