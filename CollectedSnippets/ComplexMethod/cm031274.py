def close(self):
        if self._closed:
            return
        self._closed = True

        for proto in self._pipes.values():
            if proto is None:
                continue
            # See gh-114177
            # skip closing the pipe if loop is already closed
            # this can happen e.g. when loop is closed immediately after
            # process is killed
            if self._loop and not self._loop.is_closed():
                proto.pipe.close()

        if (self._proc is not None and
                # has the child process finished?
                self._returncode is None and
                # the child process has finished, but the
                # transport hasn't been notified yet?
                self._proc.poll() is None):

            if self._loop.get_debug():
                logger.warning('Close running child process: kill %r', self)

            try:
                self._proc.kill()
            except (ProcessLookupError, PermissionError):
                # the process may have already exited or may be running setuid
                pass