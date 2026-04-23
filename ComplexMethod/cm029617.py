def _communicate(self, input, endtime, orig_timeout):
            # Start reader threads feeding into a list hanging off of this
            # object, unless they've already been started.
            if self.stdout and not hasattr(self, "_stdout_buff"):
                self._stdout_buff = []
                self.stdout_thread = \
                        threading.Thread(target=self._readerthread,
                                         args=(self.stdout, self._stdout_buff))
                self.stdout_thread.daemon = True
                self.stdout_thread.start()
            if self.stderr and not hasattr(self, "_stderr_buff"):
                self._stderr_buff = []
                self.stderr_thread = \
                        threading.Thread(target=self._readerthread,
                                         args=(self.stderr, self._stderr_buff))
                self.stderr_thread.daemon = True
                self.stderr_thread.start()

            # Start writer thread to send input to stdin, unless already
            # started.  The thread writes input and closes stdin when done,
            # or continues in the background on timeout.
            if self.stdin and not hasattr(self, "_stdin_thread"):
                self._stdin_thread = \
                        threading.Thread(target=self._writerthread,
                                         args=(input,))
                self._stdin_thread.daemon = True
                self._stdin_thread.start()

            # Wait for the writer thread, or time out.  If we time out, the
            # thread remains writing and the fd left open in case the user
            # calls communicate again.
            if hasattr(self, "_stdin_thread"):
                self._stdin_thread.join(self._remaining_time(endtime))
                if self._stdin_thread.is_alive():
                    raise TimeoutExpired(self.args, orig_timeout)

            # Wait for the reader threads, or time out.  If we time out, the
            # threads remain reading and the fds left open in case the user
            # calls communicate again.
            if self.stdout is not None:
                self.stdout_thread.join(self._remaining_time(endtime))
                if self.stdout_thread.is_alive():
                    raise TimeoutExpired(self.args, orig_timeout)
            if self.stderr is not None:
                self.stderr_thread.join(self._remaining_time(endtime))
                if self.stderr_thread.is_alive():
                    raise TimeoutExpired(self.args, orig_timeout)

            # Collect the output from and close both pipes, now that we know
            # both have been read successfully.
            stdout = None
            stderr = None
            if self.stdout:
                stdout = self._stdout_buff
                self.stdout.close()
            if self.stderr:
                stderr = self._stderr_buff
                self.stderr.close()

            # All data exchanged.  Translate lists into strings.
            stdout = stdout[0] if stdout else None
            stderr = stderr[0] if stderr else None

            return (stdout, stderr)