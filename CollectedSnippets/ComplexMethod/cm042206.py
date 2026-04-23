def evaluate(self):
    plant = Plant(
      lead_relevancy=self.lead_relevancy,
      speed=self.speed,
      distance_lead=self.distance_lead,
      enabled=self.enabled,
      only_lead2=self.only_lead2,
      only_radar=self.only_radar,
      e2e=self.e2e,
      personality=self.personality,
      force_decel=self.force_decel,
    )

    valid = True
    logs = []
    while plant.current_time < self.duration:
      speed_lead = np.interp(plant.current_time, self.breakpoints, self.speed_lead_values)
      prob_lead = np.interp(plant.current_time, self.breakpoints, self.prob_lead_values)
      cruise = np.interp(plant.current_time, self.breakpoints, self.cruise_values)
      pitch = np.interp(plant.current_time, self.breakpoints, self.pitch_values)
      prob_throttle = np.interp(plant.current_time, self.breakpoints, self.prob_throttle_values)
      log = plant.step(speed_lead, prob_lead, cruise, pitch, prob_throttle)

      d_rel = log['distance_lead'] - log['distance'] if self.lead_relevancy else 200.
      v_rel = speed_lead - log['speed'] if self.lead_relevancy else 0.
      log['d_rel'] = d_rel
      log['v_rel'] = v_rel
      logs.append(np.array([plant.current_time,
                            log['distance'],
                            log['distance_lead'],
                            log['speed'],
                            speed_lead,
                            log['acceleration'],
                            log['d_rel']]))

      if d_rel < .4 and (self.only_radar or prob_lead > 0.5):
        print("Crashed!!!!")
        valid = False

      if self.ensure_start and log['v_rel'] > 0 and log['acceleration'] < 1e-3:
        print('LongitudinalPlanner not starting!')
        valid = False

    if self.ensure_slowdown and log['speed'] > 5.5:
      print('LongitudinalPlanner not slowing down!')
      valid = False

    if self.force_decel and log['speed'] > 1e-1 and log['acceleration'] > -0.04:
      print('Not stopping with force decel')
      valid = False


    print("maneuver end", valid)
    return valid, np.array(logs)