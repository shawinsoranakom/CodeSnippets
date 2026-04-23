def sendto(self, data, addr=None):
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError('data argument must be bytes-like object (%r)',
                            type(data))

        if self._address is not None and addr not in (None, self._address):
            raise ValueError(
                f'Invalid address: must be None or {self._address}')

        if self._conn_lost and self._address:
            if self._conn_lost >= constants.LOG_THRESHOLD_FOR_CONNLOST_WRITES:
                logger.warning('socket.sendto() raised exception.')
            self._conn_lost += 1
            return

        # Ensure that what we buffer is immutable.
        self._buffer.append((bytes(data), addr))
        self._buffer_size += len(data) + self._header_size

        if self._write_fut is None:
            # No current write operations are active, kick one off
            self._loop_writing()
        # else: A write operation is already kicked off

        self._maybe_pause_protocol()