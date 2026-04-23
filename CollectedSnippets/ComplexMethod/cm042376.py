def test_init_data_values(self):
    os.environ["CLEAN"] = random.choice(["0", "1"])

    dongle  = ''.join(random.choice(string.printable) for n in range(random.randint(1, 100)))
    fake_params = [
      # param, initData field, value
      ("DongleId", "dongleId", dongle),
      ("GitCommit", "gitCommit", "commit"),
      ("GitCommitDate", "gitCommitDate", "date"),
      ("GitBranch", "gitBranch", "branch"),
      ("GitRemote", "gitRemote", "remote"),
    ]
    params = Params()
    for k, _, v in fake_params:
      params.put(k, v)
    params.put("AccessToken", "abc")

    lr = list(LogReader(str(self._gen_bootlog())))
    initData = lr[0].initData

    assert initData.dirty != bool(os.environ["CLEAN"])
    assert initData.version == get_version()

    if os.path.isfile("/proc/cmdline"):
      with open("/proc/cmdline") as f:
        assert list(initData.kernelArgs) == f.read().strip().split(" ")

      with open("/proc/version") as f:
        assert initData.kernelVersion == f.read()

    # check params
    logged_params = {entry.key: entry.value for entry in initData.params.entries}
    expected_params = {k for k, _, __ in fake_params} | {'AccessToken', 'BootCount'}
    assert set(logged_params.keys()) == expected_params, set(logged_params.keys()) ^ expected_params
    assert logged_params['AccessToken'] == b'', f"DONT_LOG param value was logged: {repr(logged_params['AccessToken'])}"
    for param_key, initData_key, v in fake_params:
      assert getattr(initData, initData_key) == v
      assert logged_params[param_key].decode() == v