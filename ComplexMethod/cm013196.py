def wrapper(self):
            if self.rank == self.MAIN_PROCESS_RANK:
                logger.debug(f"Waiting for workers to finish {self.id()}")  # noqa: G004
                # Drain all completion queues before raising any exception,
                # so stale results don't desync subsequent tests.
                deferred_exception = None
                for i, (p, completion_queue) in enumerate(
                    zip(self.processes, self.completion_queues)
                ):
                    rv = retrieve_result_from_completion_queue(
                        p, completion_queue, timeout=get_timeout(self.id())
                    )
                    if deferred_exception is not None:
                        # Already captured an exception; just drain
                        continue
                    if isinstance(rv, unittest.SkipTest):
                        deferred_exception = rv
                        continue
                    if isinstance(rv, BaseException):
                        logger.warning(
                            f"Detected failure from Rank {i} in: {self.id()}, "  # noqa: G004
                            f"skipping rest of tests in Test class: {self.__class__.__name__}"
                        )
                        self.__class__.poison_pill = True
                        deferred_exception = rv
                        continue

                    # Success
                    if rv != self.id():
                        raise AssertionError(
                            f"Expected rv == self.id(), got {rv} != {self.id()}"
                        )
                    logger.debug(
                        f"Main proc detected rank {i} finished {self.id()}"  # noqa: G004
                    )

                if deferred_exception is not None:
                    raise deferred_exception
            else:
                # Worker just runs the test
                fn()