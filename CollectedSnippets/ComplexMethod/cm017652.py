def run(self, result):
        """
        Distribute TestCases across workers.

        Return an identifier of each TestCase with its result in order to use
        imap_unordered to show results as soon as they're available.

        To minimize pickling errors when getting results from workers:

        - pass back numeric indexes in self.subsuites instead of tests
        - make tracebacks picklable with tblib, if available

        Even with tblib, errors may still occur for dynamically created
        exception classes which cannot be unpickled.
        """
        self.initialize_suite()
        counter = multiprocessing.Value(ctypes.c_int, 0)
        args = [
            (self.runner_class, index, subsuite, self.failfast, self.buffer)
            for index, subsuite in enumerate(self.subsuites)
        ]
        # Don't buffer in the main process to avoid error propagation issues.
        result.buffer = False

        with multiprocessing.Pool(
            processes=self.processes,
            initializer=functools.partial(_safe_init_worker, self.init_worker.__func__),
            initargs=[
                counter,
                self.initial_settings,
                self.serialized_contents,
                self.process_setup.__func__,
                self.process_setup_args,
                self.debug_mode,
                self.used_aliases,
            ],
        ) as pool:
            test_results = pool.imap_unordered(self.run_subsuite.__func__, args)

            while True:
                if result.shouldStop:
                    pool.terminate()
                    break

                try:
                    subsuite_index, events = test_results.next(timeout=0.1)
                except multiprocessing.TimeoutError as err:
                    if counter.value < 0:
                        err.add_note("ERROR: _init_worker failed, see prior traceback")
                        raise
                    continue
                except StopIteration:
                    pool.close()
                    break

                tests = list(self.subsuites[subsuite_index])
                for event in events:
                    self.handle_event(result, tests, event)

            pool.join()

        return result