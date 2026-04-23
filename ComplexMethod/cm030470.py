def append(self, s, charset=None, errors='strict'):
        """Append a string to the MIME header.

        Optional charset, if given, should be a Charset instance or the name
        of a character set (which will be converted to a Charset instance).  A
        value of None (the default) means that the charset given in the
        constructor is used.

        s may be a byte string or a Unicode string.  If it is a byte string
        (i.e. isinstance(s, str) is false), then charset is the encoding of
        that byte string, and a UnicodeError will be raised if the string
        cannot be decoded with that charset.  If s is a Unicode string, then
        charset is a hint specifying the character set of the characters in
        the string.  In either case, when producing an RFC 2822 compliant
        header using RFC 2047 rules, the string will be encoded using the
        output codec of the charset.  If the string cannot be encoded to the
        output codec, a UnicodeError will be raised.

        Optional 'errors' is passed as the errors argument to the decode
        call if s is a byte string.
        """
        if charset is None:
            charset = self._charset
        elif not isinstance(charset, Charset):
            charset = Charset(charset)
        if not isinstance(s, str):
            input_charset = charset.input_codec or 'us-ascii'
            if input_charset == _charset.UNKNOWN8BIT:
                s = s.decode('us-ascii', 'surrogateescape')
            else:
                s = s.decode(input_charset, errors)
        # Ensure that the bytes we're storing can be decoded to the output
        # character set, otherwise an early error is raised.
        output_charset = charset.output_codec or 'us-ascii'
        if output_charset != _charset.UNKNOWN8BIT:
            try:
                s.encode(output_charset, errors)
            except UnicodeEncodeError:
                if output_charset!='us-ascii':
                    raise
                charset = UTF8
        self._chunks.append((s, charset))