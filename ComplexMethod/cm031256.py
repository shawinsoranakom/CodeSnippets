def _do_read__buffered(self):
        offset = 0
        count = 1

        buf = self._app_protocol_get_buffer(self._get_read_buffer_size())
        wants = len(buf)

        try:
            count = self._sslobj.read(wants, buf)

            if count > 0:
                offset = count
                while offset < wants:
                    count = self._sslobj.read(wants - offset, buf[offset:])
                    if count > 0:
                        offset += count
                    else:
                        break
                else:
                    self._loop.call_soon(self._do_read)
        except SSLAgainErrors:
            pass
        if offset > 0:
            self._app_protocol_buffer_updated(offset)
        if not count:
            # close_notify
            self._call_eof_received()
            self._start_shutdown()