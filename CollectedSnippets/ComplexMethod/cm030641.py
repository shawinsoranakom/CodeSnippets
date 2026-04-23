def test_many_processes(self):
        if self.TYPE == 'threads':
            self.skipTest('test not appropriate for {}'.format(self.TYPE))

        sm = multiprocessing.get_start_method()
        N = 5 if sm == 'spawn' else 100

        # Try to overwhelm the forkserver loop with events
        procs = [self.Process(target=self._test_sleep, args=(0.01,))
                 for i in range(N)]
        for p in procs:
            p.start()
        for p in procs:
            join_process(p)
        for p in procs:
            self.assertEqual(p.exitcode, 0)

        procs = [self.Process(target=self._sleep_some)
                 for i in range(N)]
        for p in procs:
            p.start()
        time.sleep(0.001)  # let the children start...
        for p in procs:
            p.terminate()
        for p in procs:
            join_process(p)
        if os.name != 'nt':
            exitcodes = [-signal.SIGTERM]
            if sys.platform == 'darwin':
                # bpo-31510: On macOS, killing a freshly started process with
                # SIGTERM sometimes kills the process with SIGKILL.
                exitcodes.append(-signal.SIGKILL)
            for p in procs:
                self.assertIn(p.exitcode, exitcodes)