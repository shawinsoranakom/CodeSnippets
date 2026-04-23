def _worker_loop(cls, rank, world_size, rdvz_file, task_queue, completion_queue):
        raised_exception = False
        # Sub tests are going to access these values, check first
        if not (0 <= rank < world_size):
            raise AssertionError(
                f"Expected 0 <= rank < world_size, got rank={rank}, world_size={world_size}"
            )
        # set class variables for the test class
        cls.rank = rank
        cls.world_size = world_size

        # Initialize the process group
        init_skip_reason = None
        try:
            cls._init_pg(rank, world_size, rdvz_file)
        except SystemExit as ex:
            exit_code = getattr(ex, "code", None)
            skip_entry = next(
                (v for v in TEST_SKIPS.values() if v.exit_code == exit_code),
                None,
            )
            if skip_entry:
                init_skip_reason = skip_entry.message
            else:
                raise

        # End of bootstrap
        logger.debug("Setup complete")

        # Loop forever, waiting for a test name to run
        while True:
            test_id = task_queue.get()
            logger.debug(f"Got test {test_id}")  # noqa: G004
            # None means exit
            if test_id is None:
                break

            # If init failed with a skip, respond with SkipTest for all tests
            if init_skip_reason is not None:
                completion_queue.put(unittest.SkipTest(init_skip_reason))
                continue

            # Run the test
            try:
                cls._run_test_given_id(test_id)
                completion_queue.put(test_id)
            except BaseException as ex:
                if isinstance(ex, SystemExit):
                    # Get exit code from the process
                    exit_code = getattr(ex, "code", None)

                    # Look up exit code in TEST_SKIPS to see if it is a valid skip
                    skip_entry = next(
                        (v for v in TEST_SKIPS.values() if v.exit_code == exit_code),
                        None,
                    )

                    # If we found an entry, we want to skip the test and the object back to the main process
                    if skip_entry:
                        completion_queue.put(unittest.SkipTest(skip_entry.message))
                        # Skip exception handling below, move to main thread for processing the skip
                        continue

                raised_exception = True
                # Send the exception and stack trace back to the dispatcher
                exc_info = sys.exc_info()
                tb_str = "".join(traceback.format_exception(*exc_info))
                # Create a new exception with the original exception and traceback
                enhanced_ex = RuntimeError(f"Exception in worker process:\n{tb_str}")
                enhanced_ex.__cause__ = ex
                completion_queue.put(enhanced_ex)

        # Termination
        logger.debug("Terminating ...")
        # Calling destroy_process_group when workers have exceptions
        # while others are doing collectives will cause a deadlock since
        # it waits for enqueued collectives to finish.
        # Only call this on a clean exit path
        if not raised_exception:
            c10d.destroy_process_group()