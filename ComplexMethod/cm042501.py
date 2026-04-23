def update(self, sm):
    self.msg_cnt += 1

    lateralControlState = sm['controlsState'].lateralControlState
    control_type = list(lateralControlState.to_dict().keys())[0]
    control_state = lateralControlState.__getattr__(control_type)

    v_ego = sm['carState'].vEgo
    active = sm['controlsState'].active
    steer = sm['carOutput'].actuatorsOutput.torque
    standstill = sm['carState'].standstill
    steer_limited_by_safety = abs(sm['carControl'].actuators.torque - sm['carControl'].actuatorsOutput.torque) > 1e-2
    overriding = sm['carState'].steeringPressed
    changing_lanes = sm['modelV2'].meta.laneChangeState != 0
    model_points = sm['modelV2'].position.y
    # must be engaged, not at standstill, not overriding steering, and not changing lanes
    if active and not standstill and not overriding and not changing_lanes:
      self.cnt += 1

      # wait 5 seconds after engage / standstill / override / lane change
      if self.cnt >= 500:
        actual_angle = control_state.steeringAngleDeg
        desired_angle = control_state.steeringAngleDesiredDeg

        # calculate error before rounding, then round for stats grouping
        angle_error = abs(desired_angle - actual_angle)
        actual_angle = round(actual_angle, 1)
        desired_angle = round(desired_angle, 1)
        angle_error = round(angle_error, 2)
        angle_abs = int(abs(round(desired_angle, 0)))

        for group, group_props in self.all_groups.items():
          if v_ego > group_props[0]:
            # collect stats
            self.speed_group_stats[group][angle_abs]["cnt"] += 1
            self.speed_group_stats[group][angle_abs]["err"] += angle_error
            self.speed_group_stats[group][angle_abs]["steer"] += abs(steer)
            if len(model_points):
              self.speed_group_stats[group][angle_abs]["dpp"] += abs(model_points[0])
            if steer_limited_by_safety:
              self.speed_group_stats[group][angle_abs]["limited"] += 1
            if control_state.saturated:
              self.speed_group_stats[group][angle_abs]["saturated"] += 1
            if actual_angle == desired_angle:
              self.speed_group_stats[group][angle_abs]["="] += 1
            else:
              if desired_angle == 0.:
                overshoot = True
              else:
                overshoot = desired_angle < actual_angle if desired_angle > 0. else desired_angle > actual_angle
              self.speed_group_stats[group][angle_abs]["+" if overshoot else "-"] += 1
            break
    else:
      self.cnt = 0

    if self.msg_cnt % 100 == 0:
      print(chr(27) + "[2J")
      if self.cnt != 0:
        print("COLLECTING ...\n")
      else:
        print("DISABLED (not active, standstill, steering override, or lane change)\n")
      for group in self.display_groups:
        if len(self.speed_group_stats[group]) > 0:
          print(f"speed group: {group:10s} {self.all_groups[group][1]:>96s}")
          print(f"  {'-'*118}")
          for k in sorted(self.speed_group_stats[group].keys()):
            v = self.speed_group_stats[group][k]
            print(f'  {k:#2}° | actuator:{int(v["steer"] / v["cnt"] * 100):#3}% ' +
                  f'| error: {round(v["err"] / v["cnt"], 2):2.2f}° | -:{int(v["-"] / v["cnt"] * 100):#3}% ' +
                  f'| =:{int(v["="] / v["cnt"] * 100):#3}% | +:{int(v["+"] / v["cnt"] * 100):#3}% | lim:{v["limited"]:#5} ' +
                  f'| sat:{v["saturated"]:#5} | path dev: {round(v["dpp"] / v["cnt"], 2):2.2f}m | total: {v["cnt"]:#5}')
          print("")