def _write_ready(self):
        assert self._buffer, 'Data should not be empty'

        try:
            n = os.write(self._fileno, self._buffer)
        except (BlockingIOError, InterruptedError):
            pass
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as exc:
            self._buffer.clear()
            self._conn_lost += 1
            # Remove writer here, _fatal_error() doesn't it
            # because _buffer is empty.
            self._loop._remove_writer(self._fileno)
            self._fatal_error(exc, 'Fatal write error on pipe transport')
        else:
            if n == len(self._buffer):
                self._buffer.clear()
                self._loop._remove_writer(self._fileno)
                self._maybe_resume_protocol()  # May append to buffer.
                if self._closing:
                    self._loop._remove_reader(self._fileno)
                    self._call_connection_lost(None)
                return
            elif n > 0:
                del self._buffer[:n]