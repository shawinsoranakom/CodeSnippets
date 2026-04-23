def _send_output(self, message_body=None, encode_chunked=False):
        """Send the currently buffered request and clear the buffer.

        Appends an extra \\r\\n to the buffer.
        A message_body may be specified, to be appended to the request.
        """
        self._buffer.extend((b"", b""))
        msg = b"\r\n".join(self._buffer)
        del self._buffer[:]
        self.send(msg)

        if message_body is not None:

            # create a consistent interface to message_body
            if hasattr(message_body, 'read'):
                # Let file-like take precedence over byte-like.  This
                # is needed to allow the current position of mmap'ed
                # files to be taken into account.
                chunks = self._read_readable(message_body)
            else:
                try:
                    # this is solely to check to see if message_body
                    # implements the buffer API.  it /would/ be easier
                    # to capture if PyObject_CheckBuffer was exposed
                    # to Python.
                    memoryview(message_body)
                except TypeError:
                    try:
                        chunks = iter(message_body)
                    except TypeError:
                        raise TypeError("message_body should be a bytes-like "
                                        "object or an iterable, got %r"
                                        % type(message_body))
                else:
                    # the object implements the buffer interface and
                    # can be passed directly into socket methods
                    chunks = (message_body,)

            for chunk in chunks:
                if not chunk:
                    if self.debuglevel > 0:
                        print('Zero length chunk ignored')
                    continue

                if encode_chunked and self._http_vsn == 11:
                    # chunked encoding
                    chunk = f'{len(chunk):X}\r\n'.encode('ascii') + chunk \
                        + b'\r\n'
                self.send(chunk)

            if encode_chunked and self._http_vsn == 11:
                # end chunked transfer
                self.send(b'0\r\n\r\n')