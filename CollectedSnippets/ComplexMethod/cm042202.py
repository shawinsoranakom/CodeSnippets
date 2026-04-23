def test_cpu_usage(self, subtests):
    print("\n------------------------------------------------")
    print("------------------ CPU Usage -------------------")
    print("------------------------------------------------")

    plogs_by_proc = defaultdict(list)
    for pl in self.msgs['procLog']:
      for x in pl.procLog.procs:
        if len(x.cmdline) > 0:
          n = list(x.cmdline)[0]
          plogs_by_proc[n].append(x)

    cpu_ok = True
    dt = (self.msgs['procLog'][-1].logMonoTime - self.msgs['procLog'][0].logMonoTime) / 1e9
    header = ['process', 'usage', 'expected', 'max allowed', 'test result']
    rows = []
    for proc_name, expected in PROCS.items():

      error = ""
      usage = 0.
      x = plogs_by_proc[proc_name]
      if len(x) > 2:
        cpu_time = cputime_total(x[-1]) - cputime_total(x[0])
        usage = cpu_time / dt * 100.

        max_allowed = max(expected * 1.8, expected + 5.0)
        if usage > max_allowed:
          error = "❌ USING MORE CPU THAN EXPECTED ❌"
          cpu_ok = False

      else:
        error = "❌ NO METRICS FOUND ❌"
        cpu_ok = False

      rows.append([proc_name, usage, expected, max_allowed, error or "✅"])
    print(tabulate(rows, header, tablefmt="simple_grid", stralign="center", numalign="center", floatfmt=".2f"))

    # Ensure there's no missing procs
    all_procs = {p.name for p in self.msgs['managerState'][0].managerState.processes if p.shouldBeRunning}
    for p in all_procs:
      with subtests.test(proc=p):
        assert any(p in pp for pp in PROCS.keys()), f"Expected CPU usage missing for {p}"

    # total CPU check
    procs_tot = sum([(max(x) if isinstance(x, tuple) else x) for x in PROCS.values()])
    with subtests.test(name="total CPU"):
      assert procs_tot < MAX_TOTAL_CPU, "Total CPU budget exceeded"
    print("------------------------------------------------")
    print(f"Total allocated CPU usage is {procs_tot}%, budget is {MAX_TOTAL_CPU}%, {MAX_TOTAL_CPU-procs_tot:.1f}% left")
    print("------------------------------------------------")

    assert cpu_ok