def writelines(self, list_of_data):
        if self._eof:
            raise RuntimeError('Cannot call writelines() after write_eof()')
        if self._empty_waiter is not None:
            raise RuntimeError('unable to writelines; sendfile is in progress')
        if not list_of_data:
            return

        if self._conn_lost:
            if self._conn_lost >= constants.LOG_THRESHOLD_FOR_CONNLOST_WRITES:
                logger.warning('socket.send() raised exception.')
            self._conn_lost += 1
            return

        for data in list_of_data:
            self._buffer.append(memoryview(data))
            self._buffer_size += len(data)
        self._write_ready()
        # If the entire buffer couldn't be written, register a write handler
        if self._buffer:
            self._add_writer(self._sock_fd, self._write_ready)
            self._maybe_pause_protocol()