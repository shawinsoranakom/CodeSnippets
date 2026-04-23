def communicate(self, input=None, timeout=None):
        """Interact with process: Send data to stdin and close it.
        Read data from stdout and stderr, until end-of-file is
        reached.  Wait for process to terminate.

        The optional "input" argument should be data to be sent to the
        child process, or None, if no data should be sent to the child.
        communicate() returns a tuple (stdout, stderr).

        By default, all communication is in bytes, and therefore any
        "input" should be bytes, and the (stdout, stderr) will be bytes.
        If in text mode (indicated by self.text_mode), any "input" should
        be a string, and (stdout, stderr) will be strings decoded
        according to locale encoding, or by "encoding" if set. Text mode
        is triggered by setting any of text, encoding, errors or
        universal_newlines.
        """

        if self._communication_started and input:
            raise ValueError("Cannot send input after starting communication")

        # Optimization: If we are not worried about timeouts, we haven't
        # started communicating, and we have one or zero pipes, using select()
        # or threads is unnecessary.
        if (timeout is None and not self._communication_started and
            [self.stdin, self.stdout, self.stderr].count(None) >= 2):
            stdout = None
            stderr = None
            if self.stdin:
                self._stdin_write(input)
            elif self.stdout:
                stdout = self.stdout.read()
                self.stdout.close()
            elif self.stderr:
                stderr = self.stderr.read()
                self.stderr.close()
            self.wait()
        else:
            if timeout is not None:
                endtime = _time() + timeout
            else:
                endtime = None

            try:
                stdout, stderr = self._communicate(input, endtime, timeout)
            except KeyboardInterrupt:
                # https://bugs.python.org/issue25942
                # See the detailed comment in .wait().
                if timeout is not None:
                    sigint_timeout = min(self._sigint_wait_secs,
                                         self._remaining_time(endtime))
                else:
                    sigint_timeout = self._sigint_wait_secs
                self._sigint_wait_secs = 0  # nothing else should wait.
                try:
                    self._wait(timeout=sigint_timeout)
                except TimeoutExpired:
                    pass
                raise  # resume the KeyboardInterrupt

            finally:
                self._communication_started = True
            try:
                self.wait(timeout=self._remaining_time(endtime))
            except TimeoutExpired as exc:
                exc.timeout = timeout
                raise

        return (stdout, stderr)