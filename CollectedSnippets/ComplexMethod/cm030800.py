def test_above_fd_setsize(self):
        # A scalable implementation should have no problem with more than
        # FD_SETSIZE file descriptors. Since we don't know the value, we just
        # try to set the soft RLIMIT_NOFILE to the hard RLIMIT_NOFILE ceiling.
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (hard, hard))
            self.addCleanup(resource.setrlimit, resource.RLIMIT_NOFILE,
                            (soft, hard))
            NUM_FDS = min(hard, 2**16)
        except (OSError, ValueError):
            NUM_FDS = soft

        # guard for already allocated FDs (stdin, stdout...)
        NUM_FDS -= 32

        s = self.SELECTOR()
        self.addCleanup(s.close)

        for i in range(NUM_FDS // 2):
            try:
                rd, wr = self.make_socketpair()
            except OSError:
                # too many FDs, skip - note that we should only catch EMFILE
                # here, but apparently *BSD and Solaris can fail upon connect()
                # or bind() with EADDRNOTAVAIL, so let's be safe
                self.skipTest("FD limit reached")

            try:
                s.register(rd, selectors.EVENT_READ)
                s.register(wr, selectors.EVENT_WRITE)
            except OSError as e:
                if e.errno == errno.ENOSPC:
                    # this can be raised by epoll if we go over
                    # fs.epoll.max_user_watches sysctl
                    self.skipTest("FD limit reached")
                raise

        try:
            fds = s.select()
        except OSError as e:
            if e.errno == errno.EINVAL and is_apple:
                # unexplainable errors on macOS don't need to fail the test
                self.skipTest("Invalid argument error calling poll()")
            raise
        self.assertEqual(NUM_FDS // 2, len(fds))