def test_lsm6ds3_timing(self, subtests):
    # verify measurements are sampled and published at 104Hz

    sensor_t = {service: [] for service in ('accelerometer', 'gyroscope')}

    for service in sensor_t:
      for measurement in self.events.get(service, []):
        m = getattr(measurement, measurement.which())
        sensor_t[service].append(m.timestamp)

    for s, vals in sensor_t.items():
      with subtests.test(sensor=s):
        assert len(vals) > 0
        tdiffs = np.diff(vals) / 1e6 # millis

        high_delay_diffs = list(filter(lambda d: d >= 20., tdiffs))
        assert len(high_delay_diffs) < 15, f"Too many large diffs: {high_delay_diffs}"

        avg_diff = sum(tdiffs)/len(tdiffs)
        avg_freq = 1. / (avg_diff * 1e-3)
        assert 92. < avg_freq < 114., f"avg freq {avg_freq}Hz wrong, expected 104Hz"

        stddev = np.std(tdiffs)
        assert stddev < 2.0, f"Standard-dev to big {stddev}"