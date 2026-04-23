async def readuntil(self, separator=b'\n'):
        """Read data from the stream until ``separator`` is found.

        On success, the data and separator will be removed from the
        internal buffer (consumed). Returned data will include the
        separator at the end.

        Configured stream limit is used to check result. Limit sets the
        maximal length of data that can be returned, not counting the
        separator.

        If an EOF occurs and the complete separator is still not found,
        an IncompleteReadError exception will be raised, and the internal
        buffer will be reset.  The IncompleteReadError.partial attribute
        may contain the separator partially.

        If the data cannot be read because of over limit, a
        LimitOverrunError exception  will be raised, and the data
        will be left in the internal buffer, so it can be read again.

        The ``separator`` may also be a tuple of separators. In this
        case the return value will be the shortest possible that has any
        separator as the suffix. For the purposes of LimitOverrunError,
        the shortest possible separator is considered to be the one that
        matched.
        """
        if isinstance(separator, tuple):
            # Makes sure shortest matches wins
            separator = sorted(separator, key=len)
        else:
            separator = [separator]
        if not separator:
            raise ValueError('Separator should contain at least one element')
        min_seplen = len(separator[0])
        max_seplen = len(separator[-1])
        if min_seplen == 0:
            raise ValueError('Separator should be at least one-byte string')

        if self._exception is not None:
            raise self._exception

        # Consume whole buffer except last bytes, which length is
        # one less than max_seplen. Let's check corner cases with
        # separator[-1]='SEPARATOR':
        # * we have received almost complete separator (without last
        #   byte). i.e buffer='some textSEPARATO'. In this case we
        #   can safely consume max_seplen - 1 bytes.
        # * last byte of buffer is first byte of separator, i.e.
        #   buffer='abcdefghijklmnopqrS'. We may safely consume
        #   everything except that last byte, but this require to
        #   analyze bytes of buffer that match partial separator.
        #   This is slow and/or require FSM. For this case our
        #   implementation is not optimal, since require rescanning
        #   of data that is known to not belong to separator. In
        #   real world, separator will not be so long to notice
        #   performance problems. Even when reading MIME-encoded
        #   messages :)

        # `offset` is the number of bytes from the beginning of the buffer
        # where there is no occurrence of any `separator`.
        offset = 0

        # Loop until we find a `separator` in the buffer, exceed the buffer size,
        # or an EOF has happened.
        while True:
            buflen = len(self._buffer)

            # Check if we now have enough data in the buffer for shortest
            # separator to fit.
            if buflen - offset >= min_seplen:
                match_start = None
                match_end = None
                for sep in separator:
                    isep = self._buffer.find(sep, offset)

                    if isep != -1:
                        # `separator` is in the buffer. `match_start` and
                        # `match_end` will be used later to retrieve the
                        # data.
                        end = isep + len(sep)
                        if match_end is None or end < match_end:
                            match_end = end
                            match_start = isep
                if match_end is not None:
                    break

                # see upper comment for explanation.
                offset = max(0, buflen + 1 - max_seplen)
                if offset > self._limit:
                    raise exceptions.LimitOverrunError(
                        'Separator is not found, and chunk exceed the limit',
                        offset)

            # Complete message (with full separator) may be present in buffer
            # even when EOF flag is set. This may happen when the last chunk
            # adds data which makes separator be found. That's why we check for
            # EOF *after* inspecting the buffer.
            if self._eof:
                chunk = self._buffer.take_bytes()
                raise exceptions.IncompleteReadError(chunk, None)

            # _wait_for_data() will resume reading if stream was paused.
            await self._wait_for_data('readuntil')

        if match_start > self._limit:
            raise exceptions.LimitOverrunError(
                'Separator is found, but chunk is longer than limit', match_start)

        chunk = self._buffer.take_bytes(match_end)
        self._maybe_resume_transport()
        return chunk