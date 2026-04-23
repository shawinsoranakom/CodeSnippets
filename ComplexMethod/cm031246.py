def _write_send(self):
        assert self._buffer, 'Data should not be empty'
        if self._conn_lost:
            return
        try:
            buffer = self._buffer.popleft()
            n = self._sock.send(buffer)
            if n != len(buffer):
                # Not all data was written
                self._buffer.appendleft(buffer[n:])
            self._buffer_size -= n
        except (BlockingIOError, InterruptedError):
            self._buffer.appendleft(buffer)
            return
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as exc:
            self._loop._remove_writer(self._sock_fd)
            self._buffer.clear()
            self._buffer_size = 0
            self._fatal_error(exc, 'Fatal write error on socket transport')
            if self._empty_waiter is not None:
                self._empty_waiter.set_exception(exc)
        else:
            self._maybe_resume_protocol()  # May append to buffer.
            if not self._buffer:
                self._loop._remove_writer(self._sock_fd)
                if self._empty_waiter is not None:
                    self._empty_waiter.set_result(None)
                if self._closing:
                    self._call_connection_lost(None)
                elif self._eof:
                    self._sock.shutdown(socket.SHUT_WR)