def _stop_locked(
        self,
        close=os.close,
        waitpid=os.waitpid,
        waitstatus_to_exitcode=os.waitstatus_to_exitcode,
        monotonic=time.monotonic,
        sleep=time.sleep,
        WNOHANG=getattr(os, 'WNOHANG', None),
        wait_timeout=None,
    ):
        # This shouldn't happen (it might when called by a finalizer)
        # so we check for it anyway.
        if self._lock._recursion_count() > 1:
            raise self._reentrant_call_error()
        if self._fd is None:
            # not running
            return
        if self._pid is None:
            return

        # closing the "alive" file descriptor stops main()
        close(self._fd)
        self._fd = None

        try:
            if wait_timeout is None:
                _, status = waitpid(self._pid, 0)
            else:
                # gh-146313: A forked child may still hold the pipe's write
                # end open, preventing the tracker from seeing EOF and
                # exiting.  Poll with WNOHANG to avoid blocking forever.
                deadline = monotonic() + wait_timeout
                delay = 0.001
                while True:
                    result_pid, status = waitpid(self._pid, WNOHANG)
                    if result_pid != 0:
                        break
                    remaining = deadline - monotonic()
                    if remaining <= 0:
                        # The tracker is still running; it will be
                        # reparented to PID 1 (or the nearest subreaper)
                        # when we exit, and reaped there once all pipe
                        # holders release their fd.
                        self._pid = None
                        self._exitcode = None
                        self._waitpid_timed_out = True
                        return
                    delay = min(delay * 2, remaining, 0.1)
                    sleep(delay)
        except ChildProcessError:
            self._pid = None
            self._exitcode = None
            return

        self._pid = None

        try:
            self._exitcode = waitstatus_to_exitcode(status)
        except ValueError:
            # os.waitstatus_to_exitcode may raise an exception for invalid values
            self._exitcode = None