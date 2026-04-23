def _get_timedout_process_traceback(self) -> None:
        pipes = []
        for i, process in enumerate(self.processes):
            if process.exitcode is None:
                pipe = self.pid_to_pipe[process.pid]
                try:
                    pipe.send(MultiProcessTestCase.Event.GET_TRACEBACK)
                    pipes.append((i, pipe))
                except ConnectionError:
                    logger.exception(
                        "Encountered error while trying to get traceback for process %s",
                        i,
                    )

        # Wait for results.
        for rank, pipe in pipes:
            try:
                # Wait for traceback
                if pipe.poll(5):
                    if pipe.closed:
                        logger.info(
                            "Pipe closed for process %s, cannot retrieve traceback",
                            rank,
                        )
                        continue

                    traceback = pipe.recv()
                    logger.error(
                        "Process %s timed out with traceback: \n\n%s", rank, traceback
                    )
                else:
                    logger.error(
                        "Could not retrieve traceback for timed out process: %s", rank
                    )
            except ConnectionError:
                logger.exception(
                    "Encountered error while trying to get traceback for process %s",
                    rank,
                )