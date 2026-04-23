def _check_return_codes(cls, failed_ranks, timeout, fn):
        # Print based on exceptions raised from threads
        #   SkipTest: print info for each thread
        #   TimeoutError: raise RuntimeError for any timed out thread
        #   Normal Exception: print error for each thread that raises exception
        #   and raise a RuntimeError
        error_msg = ""
        skip_code = -1
        for rank, exc_info in failed_ranks:
            exc = exc_info[1]
            if isinstance(exc, unittest.SkipTest):
                logger.info(
                    "Thread %s skipping test %s for following reason: %s",
                    rank,
                    fn,
                    exc,
                )
                if skip_code < 0:
                    skip_code = TEST_SKIPS["generic"].exit_code
            elif isinstance(exc, TimeoutError):
                msg = f"Thread {rank} terminated or timed out after {timeout} seconds\n"
                logger.error(msg)
                raise RuntimeError(msg)
            elif isinstance(exc, Exception):
                msg = "".join(traceback.format_exception(*exc_info))
                logger.error("Caught exception: \n%s exiting thread %s", msg, rank)
                error_msg += f"Thread {rank} exited with exception:\n{msg}\n"
            elif isinstance(exc, SystemExit):
                if type(exc.code) is int and skip_code < 0:
                    skip_code = exc.code

        # check exceptions
        if len(error_msg) > 0:
            raise RuntimeError(error_msg)
        # check skip
        if skip_code > 0:
            for skip in TEST_SKIPS.values():
                if skip_code == skip.exit_code:
                    if IS_SANDCASTLE:
                        # "pass" the test with an appropriate message.
                        logger.info(
                            "Skipping %s on sandcastle for the following reason: %s",
                            fn,
                            skip.message,
                        )
                        return
                    else:
                        raise unittest.SkipTest(skip.message)