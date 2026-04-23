def run_scenarios(scenario, logs):
  if scenario == Scenario.BASE:
    pass

  elif scenario == Scenario.GYRO_OFF:
    logs = sorted([x for x in logs if x.which() != 'gyroscope'], key=lambda x: x.logMonoTime)

  elif scenario == Scenario.GYRO_SPIKE_MIDWAY or scenario == Scenario.GYRO_CONSISTENT_SPIKES:
    def gyro_spike(msg):
      msg.gyroscope.gyroUncalibrated.v[0] += 3.0
    count = 1 if scenario == Scenario.GYRO_SPIKE_MIDWAY else CONSISTENT_SPIKES_COUNT
    logs = modify_logs_midway(logs, 'gyroscope', count, gyro_spike)

  elif scenario == Scenario.ACCEL_OFF:
    logs = sorted([x for x in logs if x.which() != 'accelerometer'], key=lambda x: x.logMonoTime)

  elif scenario == Scenario.ACCEL_SPIKE_MIDWAY or scenario == Scenario.ACCEL_CONSISTENT_SPIKES:
    def acc_spike(msg):
      msg.accelerometer.acceleration.v[0] += 100.0
    count = 1 if scenario == Scenario.ACCEL_SPIKE_MIDWAY else CONSISTENT_SPIKES_COUNT
    logs = modify_logs_midway(logs, 'accelerometer', count, acc_spike)

  elif scenario == Scenario.SENSOR_TIMING_SPIKE_MIDWAY or scenario == Scenario.SENSOR_TIMING_CONSISTENT_SPIKES:
    def timing_spike(msg):
      msg.accelerometer.timestamp -= int(0.150 * 1e9)
    count = 1 if scenario == Scenario.SENSOR_TIMING_SPIKE_MIDWAY else CONSISTENT_SPIKES_COUNT
    logs = modify_logs_midway(logs, 'accelerometer', count, timing_spike)

  replayed_logs = replay_process_with_name(name='locationd', lr=logs)
  return get_select_fields_data(logs), get_select_fields_data(replayed_logs)