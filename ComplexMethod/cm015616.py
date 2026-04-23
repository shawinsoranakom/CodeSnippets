def test_function(self):
            for start_method, redirs in product(
                self._start_methods, redirects_oss_test()
            ):
                with self.subTest(start_method=start_method, redirs=redirs):
                    pc = start_processes(
                        name="echo",
                        entrypoint=echo1,
                        args={0: ("hello",), 1: ("hello",)},
                        envs={0: {"RANK": "0"}, 1: {"RANK": "1"}},
                        logs_specs=DefaultLogsSpecs(
                            log_dir=self.log_dir(),
                            redirects=redirs,
                        ),
                        start_method=start_method,
                    )

                    results = pc.wait(period=0.1)
                    nprocs = pc.nprocs

                    self.assert_pids_noexist(pc.pids())
                    self.assertEqual(
                        {i: f"hello_{i}" for i in range(nprocs)}, results.return_values
                    )

                    for i in range(nprocs):
                        if redirs & Std.OUT != Std.OUT:
                            self.assertFalse(results.stdouts[i])
                        if redirs & Std.ERR != Std.ERR:
                            self.assertFalse(results.stderrs[i])
                        if redirs & Std.OUT == Std.OUT:
                            self.assert_in_file(
                                [f"hello stdout from {i}"], results.stdouts[i]
                            )
                        if redirs & Std.ERR == Std.ERR:
                            self.assert_in_file(
                                [f"hello stderr from {i}"], results.stderrs[i]
                            )