def setup_class(cls):
    if "DEBUG" in os.environ:
      segs = filter(lambda x: os.path.exists(os.path.join(x, "rlog.zst")), Path(Paths.log_root()).iterdir())
      segs = sorted(segs, key=lambda x: x.stat().st_mtime)
      cls.lr = list(LogReader(os.path.join(segs[-1], "rlog.zst")))
      cls.ts = msgs_to_time_series(cls.lr)
      return

    # setup env
    params = Params()
    params.remove("CurrentRoute")
    params.put_bool("RecordFront", True)
    set_params_enabled()
    os.environ['REPLAY'] = '1'
    os.environ['MSGQ_PREALLOC'] = '1'
    os.environ['TESTING_CLOSET'] = '1'
    if os.path.exists(Paths.log_root()):
      shutil.rmtree(Paths.log_root())

    # start manager and run openpilot for TEST_DURATION
    proc = None
    try:
      manager_path = os.path.join(BASEDIR, "system/manager/manager.py")
      cls.manager_st = time.monotonic()
      proc = subprocess.Popen(["python", manager_path])

      sm = messaging.SubMaster(['carState'])
      with Timeout(30, "controls didn't start"):
        while not sm.seen['carState']:
          sm.update(1000)

      route = params.get("CurrentRoute")
      assert route is not None

      segs = list(Path(Paths.log_root()).glob(f"{route}--*"))
      assert len(segs) == 1

      time.sleep(TEST_DURATION)
    finally:
      if proc is not None:
        proc.terminate()
        if proc.wait(60) is None:
          proc.kill()

    cls.lr = list(LogReader(os.path.join(str(segs[0]), "rlog.zst")))
    st = time.monotonic()
    cls.ts = msgs_to_time_series(cls.lr)
    print("msgs to time series", time.monotonic() - st)
    log_path = segs[0]

    cls.log_sizes = {}
    for f in log_path.iterdir():
      assert f.is_file()
      cls.log_sizes[f] = f.stat().st_size / 1e6

    cls.msgs = defaultdict(list)
    for m in cls.lr:
      cls.msgs[m.which()].append(m)