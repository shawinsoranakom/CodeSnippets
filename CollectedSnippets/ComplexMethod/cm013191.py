def _check_return_codes(self, fn, elapsed_time) -> None:
        """
        Checks that the return codes of all spawned processes match, and skips
        tests if they returned a return code indicating a skipping condition.
        """
        # If no processes are spawned, there is nothing to check.
        if not self.processes:
            logger.warning(
                "Note: no subprocesses were spawned, test was likely skipped."
            )
            return

        first_process = self.processes[0]
        # first, we check if there are errors in actual processes
        # (via TEST_ERROR_EXIT CODE), and raise an exception for those.
        # the reason we do this is to attempt to raise a more helpful error
        # message than "Process x terminated/timed out"
        # TODO: we should pipe the exception of the failed subprocess here.
        # Currently, the actual exception is displayed as a logging output.
        errored_processes = [
            (i, p)
            for i, p in enumerate(self.processes)
            if p.exitcode == MultiProcessTestCase.TEST_ERROR_EXIT_CODE
        ]
        if errored_processes:
            error = ""
            for i, process in errored_processes:
                # Get error from pipe.
                error_message = self.pid_to_pipe[process.pid].recv()
                error += (
                    f"Process {i} exited with error code {MultiProcessTestCase.TEST_ERROR_EXIT_CODE} "
                    f"and exception:\n{error_message}\n"
                )

            raise RuntimeError(error)
        # If no process exited uncleanly, we check for timeouts, and then ensure
        # each process exited cleanly.
        for i, p in enumerate(self.processes):
            if p.exitcode is None:
                raise RuntimeError(
                    f"Process {i} terminated or timed out after {elapsed_time} seconds"
                )

        # Skip the test return code check
        if fn in self.skip_return_code_checks:
            return

        for skip in TEST_SKIPS.values():
            if first_process.exitcode == skip.exit_code:
                if IS_SANDCASTLE:
                    # Don't use unittest.skip to skip the test on sandcastle
                    # since it creates tasks for skipped tests assuming there
                    # is some follow-up needed. Instead just "pass" the test
                    # with an appropriate message.
                    logger.info(
                        "Skipping %s on sandcastle for the following reason: %s",
                        self.id(),
                        skip.message,
                    )
                    return
                else:
                    raise unittest.SkipTest(skip.message)

        # In most cases, we expect test to return exit code 0, standing for success.
        expected_return_code = 0
        # In some negative tests, we expect test to return non-zero exit code,
        # such as watchdog throwing SIGABRT.
        if fn in self.special_return_code_checks:
            expected_return_code = self.special_return_code_checks[fn]

        self.assertEqual(
            first_process.exitcode,
            expected_return_code,
            msg=f"Expected exit code {expected_return_code} but got {first_process.exitcode} for pid: {first_process.pid}",
        )