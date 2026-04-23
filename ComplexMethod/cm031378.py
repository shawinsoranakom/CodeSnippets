def begin(self, *, _max_headers=None):
        if self.headers is not None:
            # we've already started reading the response
            return

        # read until we get a non-100 response
        while True:
            version, status, reason = self._read_status()
            if status != CONTINUE:
                break
            # skip the header from the 100 response
            skipped_headers = _read_headers(self.fp, _max_headers)
            if self.debuglevel > 0:
                print("headers:", skipped_headers)
            del skipped_headers

        self.code = self.status = status
        self.reason = reason.strip()
        if version in ("HTTP/1.0", "HTTP/0.9"):
            # Some servers might still return "0.9", treat it as 1.0 anyway
            self.version = 10
        elif version.startswith("HTTP/1."):
            self.version = 11   # use HTTP/1.1 code for HTTP/1.x where x>=1
        else:
            raise UnknownProtocol(version)

        self.headers = self.msg = parse_headers(
            self.fp, _max_headers=_max_headers
        )

        if self.debuglevel > 0:
            for hdr, val in self.headers.items():
                print("header:", hdr + ":", val)

        # are we using the chunked-style of transfer encoding?
        tr_enc = self.headers.get("transfer-encoding")
        if tr_enc and tr_enc.lower() == "chunked":
            self.chunked = True
            self.chunk_left = None
        else:
            self.chunked = False

        # will the connection close at the end of the response?
        self.will_close = self._check_close()

        # do we have a Content-Length?
        # NOTE: RFC 2616, S4.4, #3 says we ignore this if tr_enc is "chunked"
        self.length = None
        length = self.headers.get("content-length")
        if length and not self.chunked:
            try:
                self.length = int(length)
            except ValueError:
                self.length = None
            else:
                if self.length < 0:  # ignore nonsensical negative lengths
                    self.length = None
        else:
            self.length = None

        # does the body have a fixed length? (of zero)
        if (status == NO_CONTENT or status == NOT_MODIFIED or
            100 <= status < 200 or      # 1xx codes
            self._method == "HEAD"):
            self.length = 0

        # if the connection remains open, and we aren't using chunked, and
        # a content-length was not provided, then assume that the connection
        # WILL close.
        if (not self.will_close and
            not self.chunked and
            self.length is None):
            self.will_close = True