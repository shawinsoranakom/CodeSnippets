def _copy(master_fd, master_read=_read, stdin_read=_read):
    """Parent copy loop.
    Copies
            pty master -> standard output   (master_read)
            standard input -> pty master    (stdin_read)"""
    if os.get_blocking(master_fd):
        # If we write more than tty/ndisc is willing to buffer, we may block
        # indefinitely. So we set master_fd to non-blocking temporarily during
        # the copy operation.
        os.set_blocking(master_fd, False)
        try:
            _copy(master_fd, master_read=master_read, stdin_read=stdin_read)
        finally:
            # restore blocking mode for backwards compatibility
            os.set_blocking(master_fd, True)
        return
    high_waterlevel = 4096
    stdin_avail = master_fd != STDIN_FILENO
    stdout_avail = master_fd != STDOUT_FILENO
    i_buf = b''
    o_buf = b''
    while 1:
        rfds = []
        wfds = []
        if stdin_avail and len(i_buf) < high_waterlevel:
            rfds.append(STDIN_FILENO)
        if stdout_avail and len(o_buf) < high_waterlevel:
            rfds.append(master_fd)
        if stdout_avail and len(o_buf) > 0:
            wfds.append(STDOUT_FILENO)
        if len(i_buf) > 0:
            wfds.append(master_fd)

        rfds, wfds, _xfds = select(rfds, wfds, [])

        if STDOUT_FILENO in wfds:
            try:
                n = os.write(STDOUT_FILENO, o_buf)
                o_buf = o_buf[n:]
            except OSError:
                stdout_avail = False

        if master_fd in rfds:
            # Some OSes signal EOF by returning an empty byte string,
            # some throw OSErrors.
            try:
                data = master_read(master_fd)
            except OSError:
                data = b""
            if not data:  # Reached EOF.
                return    # Assume the child process has exited and is
                          # unreachable, so we clean up.
            o_buf += data

        if master_fd in wfds:
            n = os.write(master_fd, i_buf)
            i_buf = i_buf[n:]

        if stdin_avail and STDIN_FILENO in rfds:
            data = stdin_read(STDIN_FILENO)
            if not data:
                stdin_avail = False
            else:
                i_buf += data