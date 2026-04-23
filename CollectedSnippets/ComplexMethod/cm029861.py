def read(self, size=-1, chars=-1, firstline=False):

        """ Decodes data from the stream self.stream and returns the
            resulting object.

            chars indicates the number of decoded code points or bytes to
            return. read() will never return more data than requested,
            but it might return less, if there is not enough available.

            size indicates the approximate maximum number of decoded
            bytes or code points to read for decoding. The decoder
            can modify this setting as appropriate. The default value
            -1 indicates to read and decode as much as possible.  size
            is intended to prevent having to decode huge files in one
            step.

            If firstline is true, and a UnicodeDecodeError happens
            after the first line terminator in the input only the first line
            will be returned, the rest of the input will be kept until the
            next call to read().

            The method should use a greedy read strategy, meaning that
            it should read as much data as is allowed within the
            definition of the encoding and the given size, e.g.  if
            optional encoding endings or state markers are available
            on the stream, these should be read too.
        """
        # If we have lines cached, first merge them back into characters
        if self.linebuffer:
            self.charbuffer = self._empty_charbuffer.join(self.linebuffer)
            self.linebuffer = None

        if chars < 0:
            # For compatibility with other read() methods that take a
            # single argument
            chars = size

        # read until we get the required number of characters (if available)
        while True:
            # can the request be satisfied from the character buffer?
            if chars >= 0:
                if len(self.charbuffer) >= chars:
                    break
            # we need more data
            if size < 0:
                newdata = self.stream.read()
            else:
                newdata = self.stream.read(size)
            # decode bytes (those remaining from the last call included)
            data = self.bytebuffer + newdata
            if not data:
                break
            try:
                newchars, decodedbytes = self.decode(data, self.errors)
            except UnicodeDecodeError as exc:
                if firstline:
                    newchars, decodedbytes = \
                        self.decode(data[:exc.start], self.errors)
                    lines = newchars.splitlines(keepends=True)
                    if len(lines)<=1:
                        raise
                else:
                    raise
            # keep undecoded bytes until the next call
            self.bytebuffer = data[decodedbytes:]
            # put new characters in the character buffer
            self.charbuffer += newchars
            # there was no data available
            if not newdata:
                break
        if chars < 0:
            # Return everything we've got
            result = self.charbuffer
            self.charbuffer = self._empty_charbuffer
        else:
            # Return the first chars characters
            result = self.charbuffer[:chars]
            self.charbuffer = self.charbuffer[chars:]
        return result