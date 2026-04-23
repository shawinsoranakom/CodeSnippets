def check_parallel_module_init(self, mock_os):
        if imp.lock_held():
            # This triggers on, e.g., from test import autotest.
            raise unittest.SkipTest("can't run when import lock is held")

        done = threading.Event()
        for N in (20, 50) * 3:
            if verbose:
                print("Trying", N, "threads ...", end=' ')
            # Make sure that random and modulefinder get reimported freshly
            for modname in ['random', 'modulefinder']:
                try:
                    del sys.modules[modname]
                except KeyError:
                    pass
            errors = []
            done_tasks = []
            done.clear()
            t0 = time.monotonic()
            with threading_helper.start_threads(
                    threading.Thread(target=task, args=(N, done, done_tasks, errors,))
                    for i in range(N)):
                pass
            completed = done.wait(10 * 60)
            dt = time.monotonic() - t0
            if verbose:
                print("%.1f ms" % (dt*1e3), flush=True, end=" ")
            dbg_info = 'done: %s/%s' % (len(done_tasks), N)
            self.assertFalse(errors, dbg_info)
            self.assertTrue(completed, dbg_info)
            if verbose:
                print("OK.")