def _kill_process(proc):
    """Tries to kill the process otherwise just logs a debug message, the
    process will be killed when thefuck terminates.

    :type proc: Process

    """
    try:
        proc.kill()
    except AccessDenied:
        logs.debug(u'Rerun: process PID {} ({}) could not be terminated'.format(
            proc.pid, proc.exe()))