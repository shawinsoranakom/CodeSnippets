def test_bootlog(self):
    # generate bootlog with fake launch log
    launch_log = ''.join(str(random.choice(string.printable)) for _ in range(100))
    with open("/tmp/launch_log", "w") as f:
      f.write(launch_log)

    bootlog_path = self._gen_bootlog()
    lr = list(LogReader(str(bootlog_path)))

    # check length
    assert len(lr) == 2  # boot + initData

    self._check_init_data(lr)

    # check msgs
    bootlog_msgs = [m for m in lr if m.which() == 'boot']
    assert len(bootlog_msgs) == 1

    # sanity check values
    boot = bootlog_msgs.pop().boot
    assert abs(boot.wallTimeNanos - time.time_ns()) < 5*1e9 # within 5s
    assert boot.launchLog == launch_log

    if TICI:
      for fn in ["console-ramoops", "pmsg-ramoops-0"]:
        path = Path(os.path.join("/sys/fs/pstore/", fn))
        if path.is_file():
          with open(path, "rb") as f:
            expected_val = f.read()
          bootlog_val = [e.value for e in boot.pstore.entries if e.key == fn][0]
          assert expected_val == bootlog_val
    else:
      assert len(boot.pstore.entries) == 0

    # next one should increment by one
    bl1 = re.match(RE.LOG_ID_V2, bootlog_path.name)
    bl2 = re.match(RE.LOG_ID_V2, self._gen_bootlog().name)
    assert bl1.group('uid') != bl2.group('uid')
    assert int(bl1.group('count')) == 0 and int(bl2.group('count')) == 1