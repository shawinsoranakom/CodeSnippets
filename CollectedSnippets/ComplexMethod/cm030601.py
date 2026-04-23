def test_openpty(self):
        try:
            mode = tty.tcgetattr(pty.STDIN_FILENO)
        except tty.error:
            # Not a tty or bad/closed fd.
            debug("tty.tcgetattr(pty.STDIN_FILENO) failed")
            mode = None

        new_dim = None
        if self.stdin_dim:
            try:
                # Modify pty.STDIN_FILENO window size; we need to
                # check if pty.openpty() is able to set pty slave
                # window size accordingly.
                debug("Setting pty.STDIN_FILENO window size.")
                debug(f"original size: (row, col) = {self.stdin_dim}")
                target_dim = (self.stdin_dim[0] + 1, self.stdin_dim[1] + 1)
                debug(f"target size: (row, col) = {target_dim}")
                tty.tcsetwinsize(pty.STDIN_FILENO, target_dim)

                # Were we able to set the window size
                # of pty.STDIN_FILENO successfully?
                new_dim = tty.tcgetwinsize(pty.STDIN_FILENO)
                self.assertEqual(new_dim, target_dim,
                                 "pty.STDIN_FILENO window size unchanged")
            except OSError as e:
                logging.getLogger(__name__).warning(
                    "Failed to set pty.STDIN_FILENO window size.", exc_info=e,
                )
                pass

        try:
            debug("Calling pty.openpty()")
            try:
                master_fd, slave_fd, slave_name = pty.openpty(mode, new_dim,
                                                              True)
            except TypeError:
                master_fd, slave_fd = pty.openpty()
                slave_name = None
            debug(f"Got {master_fd=}, {slave_fd=}, {slave_name=}")
        except OSError:
            # " An optional feature could not be imported " ... ?
            raise unittest.SkipTest("Pseudo-terminals (seemingly) not functional.")

        # closing master_fd can raise a SIGHUP if the process is
        # the session leader: we installed a SIGHUP signal handler
        # to ignore this signal.
        self.addCleanup(os.close, master_fd)
        self.addCleanup(os.close, slave_fd)

        self.assertTrue(os.isatty(slave_fd), "slave_fd is not a tty")

        if mode:
            self.assertEqual(tty.tcgetattr(slave_fd), mode,
                             "openpty() failed to set slave termios")
        if new_dim:
            self.assertEqual(tty.tcgetwinsize(slave_fd), new_dim,
                             "openpty() failed to set slave window size")

        # Ensure the fd is non-blocking in case there's nothing to read.
        blocking = os.get_blocking(master_fd)
        try:
            os.set_blocking(master_fd, False)
            try:
                s1 = os.read(master_fd, 1024)
                self.assertEqual(b'', s1)
            except OSError as e:
                if e.errno != errno.EAGAIN:
                    raise
        finally:
            # Restore the original flags.
            os.set_blocking(master_fd, blocking)

        debug("Writing to slave_fd")
        write_all(slave_fd, TEST_STRING_1)
        s1 = _readline(master_fd)
        self.assertEqual(b'I wish to buy a fish license.\n',
                         normalize_output(s1))

        debug("Writing chunked output")
        write_all(slave_fd, TEST_STRING_2[:5])
        write_all(slave_fd, TEST_STRING_2[5:])
        s2 = _readline(master_fd)
        self.assertEqual(b'For my pet fish, Eric.\n', normalize_output(s2))