def _spawn(shell, master_read):
    """Create a spawned process.

    Modified version of pty.spawn with terminal size support.

    """
    pid, master_fd = pty.fork()

    if pid == pty.CHILD:
        os.execlp(shell, shell)

    try:
        mode = tty.tcgetattr(pty.STDIN_FILENO)
        tty.setraw(pty.STDIN_FILENO)
        restore = True
    except tty.error:    # This is the same as termios.error
        restore = False

    _set_pty_size(master_fd)
    signal.signal(signal.SIGWINCH, lambda *_: _set_pty_size(master_fd))

    try:
        pty._copy(master_fd, master_read, pty._read)
    except OSError:
        if restore:
            tty.tcsetattr(pty.STDIN_FILENO, tty.TCSAFLUSH, mode)

    os.close(master_fd)
    return os.waitpid(pid, 0)[1]