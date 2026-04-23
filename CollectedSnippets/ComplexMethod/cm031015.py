def run_tests_sequentially(self, runtests: RunTests) -> None:
        if self.coverage:
            tracer = trace.Trace(trace=False, count=True)
        else:
            tracer = None

        save_modules = set(sys.modules)

        jobs = runtests.get_jobs()
        if jobs is not None:
            tests = count(jobs, 'test')
        else:
            tests = 'tests'
        msg = f"Run {tests} sequentially in a single process"
        if runtests.timeout:
            msg += " (timeout: %s)" % format_duration(runtests.timeout)
        self.log(msg)

        tests_iter = runtests.iter_tests()
        for test_index, test_name in enumerate(tests_iter, 1):
            start_time = time.perf_counter()

            self.logger.display_progress(test_index, test_name)

            result = self.run_test(test_name, runtests, tracer)

            # Unload the newly imported test modules (best effort finalization)
            new_modules = [module for module in sys.modules
                           if module not in save_modules and
                                module.startswith(("test.", "test_"))]
            for module in new_modules:
                sys.modules.pop(module, None)
                # Remove the attribute of the parent module.
                parent, _, name = module.rpartition('.')
                try:
                    delattr(sys.modules[parent], name)
                except (KeyError, AttributeError):
                    pass

            text = str(result)
            test_time = time.perf_counter() - start_time
            if test_time >= PROGRESS_MIN_TIME:
                text = f"{text} in {format_duration(test_time)}"
            self.logger.display_progress(test_index, text)

            if result.must_stop(self.fail_fast, self.fail_env_changed):
                break