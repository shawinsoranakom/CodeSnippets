def sendto(self, data, addr=None):
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError(f'data argument must be a bytes-like object, '
                            f'not {type(data).__name__!r}')

        if self._address:
            if addr not in (None, self._address):
                raise ValueError(
                    f'Invalid address: must be None or {self._address}')
            addr = self._address

        if self._conn_lost and self._address:
            if self._conn_lost >= constants.LOG_THRESHOLD_FOR_CONNLOST_WRITES:
                logger.warning('socket.send() raised exception.')
            self._conn_lost += 1
            return

        if not self._buffer:
            # Attempt to send it right away first.
            try:
                if self._extra['peername']:
                    self._sock.send(data)
                else:
                    self._sock.sendto(data, addr)
                return
            except (BlockingIOError, InterruptedError):
                self._add_writer(self._sock_fd, self._sendto_ready)
            except OSError as exc:
                self._protocol.error_received(exc)
                return
            except (SystemExit, KeyboardInterrupt):
                raise
            except BaseException as exc:
                self._fatal_error(
                    exc, 'Fatal write error on datagram transport')
                return

        # Ensure that what we buffer is immutable.
        self._buffer.append((bytes(data), addr))
        self._buffer_size += len(data) + self._header_size
        self._maybe_pause_protocol()