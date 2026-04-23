def _join_processes(self, fn) -> None:
        timeout = get_timeout(self.id())
        start_time = time.time()
        subprocess_error = False
        try:
            while True:
                # check to see if any subprocess exited with an error early.
                for i, p in enumerate(self.processes):
                    # This is the exit code processes exit with if they
                    # encountered an exception.
                    if p.exitcode == MultiProcessTestCase.TEST_ERROR_EXIT_CODE:
                        print(
                            f"Process {i} terminated with exit code {p.exitcode}, terminating remaining processes."
                        )
                        active_children = torch.multiprocessing.active_children()
                        for ac in active_children:
                            ac.terminate()
                        subprocess_error = True
                        break
                if subprocess_error:
                    break
                # All processes have joined cleanly if they all a valid exitcode
                if all(p.exitcode is not None for p in self.processes):
                    break
                # Check if we should time out the test. If so, we terminate each process.
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    self._get_timedout_process_traceback()
                    print(
                        f"Timing out after {timeout} seconds and killing subprocesses."
                    )
                    for p in self.processes:
                        p.terminate()
                    break
                # Sleep to avoid excessive busy polling.
                time.sleep(0.1)

            elapsed_time = time.time() - start_time
            self._check_return_codes(fn, elapsed_time)
        finally:
            # Close all pipes
            for pipe in self.pid_to_pipe.values():
                pipe.close()