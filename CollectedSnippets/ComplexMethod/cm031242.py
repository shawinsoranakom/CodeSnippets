def _read_ready__get_buffer(self):
        if self._conn_lost:
            return

        try:
            buf = self._protocol.get_buffer(-1)
            if not len(buf):
                raise RuntimeError('get_buffer() returned an empty buffer')
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as exc:
            self._fatal_error(
                exc, 'Fatal error: protocol.get_buffer() call failed.')
            return

        try:
            nbytes = self._sock.recv_into(buf)
        except (BlockingIOError, InterruptedError):
            return
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as exc:
            self._fatal_error(exc, 'Fatal read error on socket transport')
            return

        if not nbytes:
            self._read_ready__on_eof()
            return

        try:
            self._protocol.buffer_updated(nbytes)
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as exc:
            self._fatal_error(
                exc, 'Fatal error: protocol.buffer_updated() call failed.')