def wait_process(pid, *, exitcode, timeout=None):
    """
    Wait until process pid completes and check that the process exit code is
    exitcode.

    Raise an AssertionError if the process exit code is not equal to exitcode.

    If the process runs longer than timeout seconds (LONG_TIMEOUT by default),
    kill the process (if signal.SIGKILL is available) and raise an
    AssertionError. The timeout feature is not available on Windows.
    """
    if os.name != "nt":
        import signal

        if timeout is None:
            timeout = LONG_TIMEOUT

        start_time = time.monotonic()
        for _ in sleeping_retry(timeout, error=False):
            pid2, status = os.waitpid(pid, os.WNOHANG)
            if pid2 != 0:
                break
            # rety: the process is still running
        else:
            try:
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
            except OSError:
                # Ignore errors like ChildProcessError or PermissionError
                pass

            dt = time.monotonic() - start_time
            raise AssertionError(f"process {pid} is still running "
                                 f"after {dt:.1f} seconds")
    else:
        # Windows implementation: don't support timeout :-(
        pid2, status = os.waitpid(pid, 0)

    exitcode2 = os.waitstatus_to_exitcode(status)
    if exitcode2 != exitcode:
        raise AssertionError(f"process {pid} exited with code {exitcode2}, "
                             f"but exit code {exitcode} is expected")

    # sanity check: it should not fail in practice
    if pid2 != pid:
        raise AssertionError(f"pid {pid2} != pid {pid}")