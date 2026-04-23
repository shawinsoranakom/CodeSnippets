def __str__(self):
        """Return the string value of the header."""
        self._normalize()
        uchunks = []
        lastcs = None
        lastspace = None
        for string, charset in self._chunks:
            # We must preserve spaces between encoded and non-encoded word
            # boundaries, which means for us we need to add a space when we go
            # from a charset to None/us-ascii, or from None/us-ascii to a
            # charset.  Only do this for the second and subsequent chunks.
            # Don't add a space if the None/us-ascii string already has
            # a space (trailing or leading depending on transition)
            nextcs = charset
            if nextcs == _charset.UNKNOWN8BIT:
                original_bytes = string.encode('ascii', 'surrogateescape')
                string = original_bytes.decode('ascii', 'replace')
            if uchunks:
                hasspace = string and self._nonctext(string[0])
                if lastcs not in (None, 'us-ascii'):
                    if nextcs in (None, 'us-ascii') and not hasspace:
                        uchunks.append(SPACE)
                        nextcs = None
                elif nextcs not in (None, 'us-ascii') and not lastspace:
                    uchunks.append(SPACE)
            lastspace = string and self._nonctext(string[-1])
            lastcs = nextcs
            uchunks.append(string)
        return EMPTYSTRING.join(uchunks)