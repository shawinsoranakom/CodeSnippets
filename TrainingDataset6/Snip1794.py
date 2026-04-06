def _set_pty_size(master_fd):
    buf = array.array('h', [0, 0, 0, 0])
    fcntl.ioctl(pty.STDOUT_FILENO, termios.TIOCGWINSZ, buf, True)
    fcntl.ioctl(master_fd, termios.TIOCSWINSZ, buf)