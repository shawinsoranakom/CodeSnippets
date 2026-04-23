def join(self, timeout: float | None = None, grace_period: float | None = None):
        r"""Join one or more processes within spawn context.

        Attempt to join one or more processes in this spawn context.
        If one of them exited with a non-zero exit status, this function
        kills the remaining processes (optionally with a grace period)
        and raises an exception with the cause of the first process exiting.

        Returns ``True`` if all processes have been joined successfully,
        ``False`` if there are more processes that need to be joined.

        Args:
            timeout (float): Wait this long (in seconds) before giving up on waiting.
            grace_period (float): When any processes fail, wait this long (in seconds)
                for others to shutdown gracefully before terminating them. If they
                still don't exit, wait another grace period before killing them.
        """
        # Ensure this function can be called even when we're done.
        if len(self.sentinels) == 0:
            return True

        # Wait for any process to fail or all of them to succeed.
        ready = multiprocessing.connection.wait(
            self.sentinels.keys(),
            timeout=timeout,
        )

        error_index = None
        for sentinel in ready:
            index = self.sentinels.pop(sentinel)
            process = self.processes[index]
            process.join()
            if process.exitcode != 0:
                error_index = index
                break

        # Return if there was no error.
        if error_index is None:
            # Return whether or not all processes have been joined.
            return len(self.sentinels) == 0
        # An error occurred. Clean-up all processes before returning.
        # First, allow a grace period for processes to shutdown themselves.
        if grace_period is not None:
            self._join_procs_with_timeout(grace_period)
        # Then, terminate processes that are still alive. Try SIGTERM first.
        for process in self.processes:
            if process.is_alive():
                log.warning("Terminating process %s via signal SIGTERM", process.pid)
                process.terminate()

        # Try SIGKILL if the process isn't going down after another grace_period.
        # The reason is related to python signal handling is limited
        # to main thread and if that is in c/c++ land and stuck it won't
        # to handle it. We have seen processes getting stuck not handling
        # SIGTERM for the above reason.
        self._join_procs_with_timeout(30 if grace_period is None else grace_period)
        for process in self.processes:
            if process.is_alive():
                log.warning(
                    "Unable to shutdown process %s via SIGTERM , forcefully exiting via SIGKILL",
                    process.pid,
                )
                process.kill()
            process.join()

        # The file will only be created if the process crashed.
        failed_process = self.processes[error_index]
        if not os.access(self.error_files[error_index], os.R_OK):
            exitcode = self.processes[error_index].exitcode
            if exitcode < 0:
                try:
                    name = signal.Signals(-exitcode).name
                except ValueError:
                    name = f"<Unknown signal {-exitcode}>"
                raise ProcessExitedException(
                    f"process {error_index:d} terminated with signal {name}",
                    error_index=error_index,
                    error_pid=failed_process.pid,
                    exit_code=exitcode,
                    signal_name=name,
                )
            else:
                raise ProcessExitedException(
                    f"process {error_index:d} terminated with exit code {exitcode:d}",
                    error_index=error_index,
                    error_pid=failed_process.pid,
                    exit_code=exitcode,
                )

        with open(self.error_files[error_index], "rb") as fh:
            original_trace = pickle.load(fh)
        msg = f"\n\n-- Process {error_index:d} terminated with the following error:\n"
        msg += original_trace
        raise ProcessRaisedException(msg, error_index, failed_process.pid)