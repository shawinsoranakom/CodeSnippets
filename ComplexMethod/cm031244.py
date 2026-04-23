def write(self, data):
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError(f'data argument must be a bytes, bytearray, or memoryview '
                            f'object, not {type(data).__name__!r}')
        if self._eof:
            raise RuntimeError('Cannot call write() after write_eof()')
        if self._empty_waiter is not None:
            raise RuntimeError('unable to write; sendfile is in progress')
        if not data:
            return

        if self._conn_lost:
            if self._conn_lost >= constants.LOG_THRESHOLD_FOR_CONNLOST_WRITES:
                logger.warning('socket.send() raised exception.')
            self._conn_lost += 1
            return

        if not self._buffer:
            # Optimization: try to send now.
            try:
                n = self._sock.send(data)
            except (BlockingIOError, InterruptedError):
                pass
            except (SystemExit, KeyboardInterrupt):
                raise
            except BaseException as exc:
                self._fatal_error(exc, 'Fatal write error on socket transport')
                return
            else:
                data = memoryview(data)[n:]
                if not data:
                    return
            # Not all was written; register write handler.
            self._add_writer(self._sock_fd, self._write_ready)

        # Add it to the buffer.
        self._buffer.append(data)
        self._buffer_size += len(data)
        self._maybe_pause_protocol()