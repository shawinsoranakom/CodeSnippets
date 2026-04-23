def _internal_poll(self, _deadstate=None, _del_safe=_del_safe):
            """Check if child process has terminated.  Returns returncode
            attribute.

            This method is called by __del__, so it cannot reference anything
            outside of the local scope (nor can any methods it calls).

            """
            if self.returncode is None:
                if not self._waitpid_lock.acquire(False):
                    # Something else is busy calling waitpid.  Don't allow two
                    # at once.  We know nothing yet.
                    return None
                try:
                    if self.returncode is not None:
                        return self.returncode  # Another thread waited.
                    pid, sts = _del_safe.waitpid(self.pid, _del_safe.WNOHANG)
                    if pid == self.pid:
                        self._handle_exitstatus(sts)
                except OSError as e:
                    if _deadstate is not None:
                        self.returncode = _deadstate
                    elif e.errno == _del_safe.ECHILD:
                        # This happens if SIGCLD is set to be ignored or
                        # waiting for child processes has otherwise been
                        # disabled for our process.  This child is dead, we
                        # can't get the status.
                        # http://bugs.python.org/issue15756
                        self.returncode = 0
                finally:
                    self._waitpid_lock.release()
            return self.returncode