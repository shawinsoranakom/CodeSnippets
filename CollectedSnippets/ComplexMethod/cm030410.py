def run(self, test):
        "Run the given test case or test suite."
        result = self._makeResult()
        registerResult(result)
        result.failfast = self.failfast
        result.buffer = self.buffer
        result.tb_locals = self.tb_locals
        with warnings.catch_warnings():
            if self.warnings:
                # if self.warnings is set, use it to filter all the warnings
                warnings.simplefilter(self.warnings)
            start_time = time.perf_counter()
            startTestRun = getattr(result, 'startTestRun', None)
            if startTestRun is not None:
                startTestRun()
            try:
                test(result)
            finally:
                stopTestRun = getattr(result, 'stopTestRun', None)
                if stopTestRun is not None:
                    stopTestRun()
            stop_time = time.perf_counter()
        time_taken = stop_time - start_time
        result.printErrors()
        if self.durations is not None:
            self._printDurations(result)

        if hasattr(result, 'separator2'):
            self.stream.writeln(result.separator2)

        run = result.testsRun
        self.stream.writeln("Ran %d test%s in %.3fs" %
                            (run, run != 1 and "s" or "", time_taken))
        self.stream.writeln()

        expected_fails = unexpected_successes = skipped = 0
        try:
            results = map(len, (result.expectedFailures,
                                result.unexpectedSuccesses,
                                result.skipped))
        except AttributeError:
            pass
        else:
            expected_fails, unexpected_successes, skipped = results

        infos = []
        t = get_theme(tty_file=self.stream).unittest

        if not result.wasSuccessful():
            self.stream.write(f"{t.fail_info}FAILED{t.reset}")
            failed, errored = len(result.failures), len(result.errors)
            if failed:
                infos.append(f"{t.fail_info}failures={failed}{t.reset}")
            if errored:
                infos.append(f"{t.fail_info}errors={errored}{t.reset}")
        elif run == 0 and not skipped:
            self.stream.write(f"{t.warn}NO TESTS RAN{t.reset}")
        else:
            self.stream.write(f"{t.passed}OK{t.reset}")
        if skipped:
            infos.append(f"{t.warn}skipped={skipped}{t.reset}")
        if expected_fails:
            infos.append(f"{t.warn}expected failures={expected_fails}{t.reset}")
        if unexpected_successes:
            infos.append(
                f"{t.fail}unexpected successes={unexpected_successes}{t.reset}"
            )
        if infos:
            self.stream.writeln(" (%s)" % (", ".join(infos),))
        else:
            self.stream.write("\n")
        self.stream.flush()
        return result