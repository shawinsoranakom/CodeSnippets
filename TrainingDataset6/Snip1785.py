def _get_shell_pid():
    """Returns parent process pid."""
    proc = Process(os.getpid())

    try:
        return proc.parent().pid
    except TypeError:
        return proc.parent.pid