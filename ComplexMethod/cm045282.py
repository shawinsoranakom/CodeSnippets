async def _execute_command(self, command: List[str], cancellation_token: CancellationToken) -> Tuple[str, int]:
        if self._container is None or not self._running:
            raise ValueError("Container is not running. Must first be started with either start or a context manager.")

        exec_task = asyncio.create_task(asyncio.to_thread(self._container.exec_run, command))
        cancellation_token.link_future(exec_task)

        # Wait for the exec task to finish.
        try:
            result = await exec_task
            exit_code = result.exit_code
            output = result.output.decode("utf-8")
            if exit_code == 124:
                output += "\n Timeout"
            return output, exit_code
        except asyncio.CancelledError:
            # Schedule a task to kill the running command in the background.
            if self._loop and not self._loop.is_closed():
                try:
                    logging.debug(f"Scheduling kill command via run_coroutine_threadsafe on loop {self._loop!r}")
                    future: ConcurrentFuture[None] = asyncio.run_coroutine_threadsafe(
                        self._kill_running_command(command), self._loop
                    )
                    self._cancellation_futures.append(future)
                    logging.debug(f"Kill command scheduled, future: {future!r}")
                except RuntimeError as e:
                    logging.error(f"Failed to schedule kill command on loop {self._loop!r}: {e}")
                except Exception as e:
                    logging.exception(f"Unexpected error scheduling kill command: {e}")
            else:
                logging.warning(
                    f"Cannot schedule kill command: Executor loop is not available or closed (loop: {self._loop!r})."
                )
            return "Code execution was cancelled.", 1