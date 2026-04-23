def _wait(self, timeout):
            """Internal implementation of wait() on POSIX.

            Uses efficient pidfd_open() + poll() on Linux or kqueue()
            on macOS/BSD when available. Falls back to polling
            waitpid(WNOHANG) otherwise.
            """
            if self.returncode is not None:
                return self.returncode

            if timeout is not None:
                if timeout < 0:
                    raise TimeoutExpired(self.args, timeout)
                started = _time()
                endtime = started + timeout

                # Try efficient wait first.
                if self._wait_pidfd(timeout) or self._wait_kqueue(timeout):
                    # Process is gone. At this point os.waitpid(pid, 0)
                    # will return immediately, but in very rare races
                    # the PID may have been reused.
                    # os.waitpid(pid, WNOHANG) ensures we attempt a
                    # non-blocking reap without blocking indefinitely.
                    with self._waitpid_lock:
                        if self.returncode is not None:
                            return self.returncode  # Another thread waited.
                        (pid, sts) = self._try_wait(os.WNOHANG)
                        assert pid == self.pid or pid == 0
                        if pid == self.pid:
                            self._handle_exitstatus(sts)
                            return self.returncode
                        # os.waitpid(pid, WNOHANG) returned 0 instead
                        # of our PID, meaning PID has not yet exited,
                        # even though poll() / kqueue() said so. Very
                        # rare and mostly theoretical. Fallback to busy
                        # polling.
                        elapsed = _time() - started
                        endtime -= elapsed

                # Enter a busy loop if we have a timeout.  This busy loop was
                # cribbed from Lib/threading.py in Thread.wait() at r71065.
                delay = 0.0005 # 500 us -> initial delay of 1 ms
                while True:
                    if self._waitpid_lock.acquire(False):
                        try:
                            if self.returncode is not None:
                                break  # Another thread waited.
                            (pid, sts) = self._try_wait(os.WNOHANG)
                            assert pid == self.pid or pid == 0
                            if pid == self.pid:
                                self._handle_exitstatus(sts)
                                break
                        finally:
                            self._waitpid_lock.release()
                    remaining = self._remaining_time(endtime)
                    if remaining <= 0:
                        raise TimeoutExpired(self.args, timeout)
                    delay = min(delay * 2, remaining, .05)
                    time.sleep(delay)
            else:
                while self.returncode is None:
                    with self._waitpid_lock:
                        if self.returncode is not None:
                            break  # Another thread waited.
                        (pid, sts) = self._try_wait(0)
                        # Check the pid and loop as waitpid has been known to
                        # return 0 even without WNOHANG in odd situations.
                        # http://bugs.python.org/issue14396.
                        if pid == self.pid:
                            self._handle_exitstatus(sts)

            return self.returncode