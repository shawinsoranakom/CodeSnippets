def test_timings(self):
    passed = True
    print("\n------------------------------------------------")
    print("----------------- Service Timings --------------")
    print("------------------------------------------------")

    header = ['service', 'max', 'min', 'mean', 'expected mean', 'rsd', 'max allowed rsd', 'test result']
    rows = []
    for s, (maxmin, rsd) in TIMINGS.items():
      offset = int(SERVICE_LIST[s].frequency * LOG_OFFSET)
      msgs = [m.logMonoTime for m in self.msgs[s][offset:]]
      if not len(msgs):
        raise Exception(f"missing {s}")

      ts = np.diff(msgs) / 1e9
      dt = 1 / SERVICE_LIST[s].frequency

      errors = []
      if not np.allclose(np.mean(ts), dt, rtol=0.03, atol=0):
        errors.append("❌ FAILED MEAN TIMING CHECK ❌")
      if not np.allclose([np.max(ts), np.min(ts)], dt, rtol=maxmin, atol=0):
        errors.append("❌ FAILED MAX/MIN TIMING CHECK ❌")
      if (np.std(ts)/dt) > rsd:
        errors.append("❌ FAILED RSD TIMING CHECK ❌")
      passed = not errors and passed
      rows.append([s, *(np.array([np.max(ts), np.min(ts), np.mean(ts), dt])*1e3), np.std(ts)/dt, rsd, "\n".join(errors) or "✅"])

    print(tabulate(rows, header, tablefmt="simple_grid", stralign="center", numalign="center", floatfmt=".2f"))
    assert passed