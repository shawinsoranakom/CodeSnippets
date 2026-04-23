def _run_tests(self, selected: TestTuple, tests: TestList | None) -> int:
        if self.hunt_refleak and self.hunt_refleak.warmups < 3:
            msg = ("WARNING: Running tests with --huntrleaks/-R and "
                   "less than 3 warmup repetitions can give false positives!")
            print(msg, file=sys.stdout, flush=True)

        if self.num_workers < 0:
            # Use all CPUs + 2 extra worker processes for tests
            # that like to sleep
            #
            # os.process.cpu_count() is new in Python 3.13;
            # mypy doesn't know about it yet
            self.num_workers = (os.process_cpu_count() or 1) + 2  # type: ignore[attr-defined]

        # For a partial run, we do not need to clutter the output.
        if (self.want_header
            or not(self.pgo or self.quiet or self.single_test_run
                   or tests or self.cmdline_args)):
            display_header(self.use_resources, self.python_cmd)

        print("Using random seed:", self.random_seed)

        runtests = self.create_run_tests(selected)
        self.first_runtests = runtests
        self.logger.set_tests(runtests)

        if (runtests.hunt_refleak is not None) and (not self.num_workers):
            # gh-109739: WindowsLoadTracker thread interferes with refleak check
            use_load_tracker = False
        else:
            # WindowsLoadTracker is only needed on Windows
            use_load_tracker = MS_WINDOWS

        if use_load_tracker:
            self.logger.start_load_tracker()
        try:
            if self.num_workers:
                self._run_tests_mp(runtests, self.num_workers)
            else:
                self.run_tests_sequentially(runtests)

            coverage = self.results.get_coverage_results()
            self.display_result(runtests)

            if self.want_rerun and self.results.need_rerun():
                self.rerun_failed_tests(runtests)

            if self.want_bisect and self.results.need_rerun():
                self.run_bisect(runtests)
        finally:
            if use_load_tracker:
                self.logger.stop_load_tracker()

        self.display_summary()
        self.finalize_tests(coverage)

        return self.results.get_exitcode(self.fail_env_changed,
                                         self.fail_rerun)