def _loop_writing(self, fut=None):
        try:
            if self._conn_lost:
                return

            assert fut is self._write_fut
            self._write_fut = None
            if fut:
                # We are in a _loop_writing() done callback, get the result
                fut.result()

            if not self._buffer or (self._conn_lost and self._address):
                # The connection has been closed
                if self._closing:
                    self._loop.call_soon(self._call_connection_lost, None)
                return

            data, addr = self._buffer.popleft()
            self._buffer_size -= len(data) + self._header_size
            if self._address is not None:
                self._write_fut = self._loop._proactor.send(self._sock,
                                                            data)
            else:
                self._write_fut = self._loop._proactor.sendto(self._sock,
                                                              data,
                                                              addr=addr)
        except OSError as exc:
            self._protocol.error_received(exc)
        except Exception as exc:
            self._fatal_error(exc, 'Fatal write error on datagram transport')
        else:
            self._write_fut.add_done_callback(self._loop_writing)
            self._maybe_resume_protocol()