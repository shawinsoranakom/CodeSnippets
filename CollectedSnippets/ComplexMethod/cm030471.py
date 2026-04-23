def encode(self, splitchars=';, \t', maxlinelen=None, linesep='\n'):
        r"""Encode a message header into an RFC-compliant format.

        There are many issues involved in converting a given string for use in
        an email header.  Only certain character sets are readable in most
        email clients, and as header strings can only contain a subset of
        7-bit ASCII, care must be taken to properly convert and encode (with
        Base64 or quoted-printable) header strings.  In addition, there is a
        75-character length limit on any given encoded header field, so
        line-wrapping must be performed, even with double-byte character sets.

        Optional maxlinelen specifies the maximum length of each generated
        line, exclusive of the linesep string.  Individual lines may be longer
        than maxlinelen if a folding point cannot be found.  The first line
        will be shorter by the length of the header name plus ": " if a header
        name was specified at Header construction time.  The default value for
        maxlinelen is determined at header construction time.

        Optional splitchars is a string containing characters which should be
        given extra weight by the splitting algorithm during normal header
        wrapping.  This is in very rough support of RFC 2822's 'higher level
        syntactic breaks':  split points preceded by a splitchar are preferred
        during line splitting, with the characters preferred in the order in
        which they appear in the string.  Space and tab may be included in the
        string to indicate whether preference should be given to one over the
        other as a split point when other split chars do not appear in the line
        being split.  Splitchars does not affect RFC 2047 encoded lines.

        Optional linesep is a string to be used to separate the lines of
        the value.  The default value is the most useful for typical
        Python applications, but it can be set to \r\n to produce RFC-compliant
        line separators when needed.
        """
        self._normalize()
        if maxlinelen is None:
            maxlinelen = self._maxlinelen
        # A maxlinelen of 0 means don't wrap.  For all practical purposes,
        # choosing a huge number here accomplishes that and makes the
        # _ValueFormatter algorithm much simpler.
        if maxlinelen == 0:
            maxlinelen = 1000000
        formatter = _ValueFormatter(self._headerlen, maxlinelen,
                                    self._continuation_ws, splitchars)
        lastcs = None
        hasspace = lastspace = None
        for string, charset in self._chunks:
            if hasspace is not None:
                hasspace = string and self._nonctext(string[0])
                if lastcs not in (None, 'us-ascii'):
                    if not hasspace or charset not in (None, 'us-ascii'):
                        formatter.add_transition()
                elif charset not in (None, 'us-ascii') and not lastspace:
                    formatter.add_transition()
            lastspace = string and self._nonctext(string[-1])
            lastcs = charset
            hasspace = False
            lines = string.splitlines()
            if lines:
                formatter.feed('', lines[0], charset)
            else:
                formatter.feed('', '', charset)
            for line in lines[1:]:
                formatter.newline()
                if charset.header_encoding is not None:
                    formatter.feed(self._continuation_ws, ' ' + line.lstrip(),
                                   charset)
                else:
                    sline = line.lstrip()
                    fws = line[:len(line)-len(sline)]
                    formatter.feed(fws, sline, charset)
            if len(lines) > 1:
                formatter.newline()
        if self._chunks:
            formatter.add_transition()
        value = formatter._str(linesep)
        if _embedded_header.search(value):
            raise HeaderParseError("header value appears to contain "
                "an embedded header: {!r}".format(value))
        return value