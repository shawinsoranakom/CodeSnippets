def readline(self, size=None, keepends=True):

        """ Read one line from the input stream and return the
            decoded data.

            size, if given, is passed as size argument to the
            read() method.

        """
        # If we have lines cached from an earlier read, return
        # them unconditionally
        if self.linebuffer:
            line = self.linebuffer[0]
            del self.linebuffer[0]
            if len(self.linebuffer) == 1:
                # revert to charbuffer mode; we might need more data
                # next time
                self.charbuffer = self.linebuffer[0]
                self.linebuffer = None
            if not keepends:
                line = line.splitlines(keepends=False)[0]
            return line

        readsize = size or 72
        line = self._empty_charbuffer
        # If size is given, we call read() only once
        while True:
            data = self.read(readsize, firstline=True)
            if data:
                # If we're at a "\r" read one extra character (which might
                # be a "\n") to get a proper line ending. If the stream is
                # temporarily exhausted we return the wrong line ending.
                if (isinstance(data, str) and data.endswith("\r")) or \
                   (isinstance(data, bytes) and data.endswith(b"\r")):
                    data += self.read(size=1, chars=1)

            line += data
            lines = line.splitlines(keepends=True)
            if lines:
                if len(lines) > 1:
                    # More than one line result; the first line is a full line
                    # to return
                    line = lines[0]
                    del lines[0]
                    if len(lines) > 1:
                        # cache the remaining lines
                        lines[-1] += self.charbuffer
                        self.linebuffer = lines
                        self.charbuffer = None
                    else:
                        # only one remaining line, put it back into charbuffer
                        self.charbuffer = lines[0] + self.charbuffer
                    if not keepends:
                        line = line.splitlines(keepends=False)[0]
                    break
                line0withend = lines[0]
                line0withoutend = lines[0].splitlines(keepends=False)[0]
                if line0withend != line0withoutend: # We really have a line end
                    # Put the rest back together and keep it until the next call
                    self.charbuffer = self._empty_charbuffer.join(lines[1:]) + \
                                      self.charbuffer
                    if keepends:
                        line = line0withend
                    else:
                        line = line0withoutend
                    break
            # we didn't get anything or this was our only try
            if not data or size is not None:
                if line and not keepends:
                    line = line.splitlines(keepends=False)[0]
                break
            if readsize < 8000:
                readsize *= 2
        return line