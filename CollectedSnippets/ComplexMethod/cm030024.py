def _proc_pax(self, tarfile):
        """Process an extended or global header as described in
           POSIX.1-2008.
        """
        # Read the header information.
        buf = tarfile.fileobj.read(self._block(self.size))

        # A pax header stores supplemental information for either
        # the following file (extended) or all following files
        # (global).
        if self.type == XGLTYPE:
            pax_headers = tarfile.pax_headers
        else:
            pax_headers = tarfile.pax_headers.copy()

        # Parse pax header information. A record looks like that:
        # "%d %s=%s\n" % (length, keyword, value). length is the size
        # of the complete record including the length field itself and
        # the newline.
        pos = 0
        encoding = None
        raw_headers = []
        while len(buf) > pos and buf[pos] != 0x00:
            if not (match := _header_length_prefix_re.match(buf, pos)):
                raise InvalidHeaderError("invalid header")
            try:
                length = int(match.group(1))
            except ValueError:
                raise InvalidHeaderError("invalid header")
            # Headers must be at least 5 bytes, shortest being '5 x=\n'.
            # Value is allowed to be empty.
            if length < 5:
                raise InvalidHeaderError("invalid header")
            if pos + length > len(buf):
                raise InvalidHeaderError("invalid header")

            header_value_end_offset = match.start(1) + length - 1  # Last byte of the header
            keyword_and_value = buf[match.end(1) + 1:header_value_end_offset]
            raw_keyword, equals, raw_value = keyword_and_value.partition(b"=")

            # Check the framing of the header. The last character must be '\n' (0x0A)
            if not raw_keyword or equals != b"=" or buf[header_value_end_offset] != 0x0A:
                raise InvalidHeaderError("invalid header")
            raw_headers.append((length, raw_keyword, raw_value))

            # Check if the pax header contains a hdrcharset field. This tells us
            # the encoding of the path, linkpath, uname and gname fields. Normally,
            # these fields are UTF-8 encoded but since POSIX.1-2008 tar
            # implementations are allowed to store them as raw binary strings if
            # the translation to UTF-8 fails. For the time being, we don't care about
            # anything other than "BINARY". The only other value that is currently
            # allowed by the standard is "ISO-IR 10646 2000 UTF-8" in other words UTF-8.
            # Note that we only follow the initial 'hdrcharset' setting to preserve
            # the initial behavior of the 'tarfile' module.
            if raw_keyword == b"hdrcharset" and encoding is None:
                if raw_value == b"BINARY":
                    encoding = tarfile.encoding
                else:  # This branch ensures only the first 'hdrcharset' header is used.
                    encoding = "utf-8"

            pos += length

        # If no explicit hdrcharset is set, we use UTF-8 as a default.
        if encoding is None:
            encoding = "utf-8"

        # After parsing the raw headers we can decode them to text.
        for length, raw_keyword, raw_value in raw_headers:
            # Normally, we could just use "utf-8" as the encoding and "strict"
            # as the error handler, but we better not take the risk. For
            # example, GNU tar <= 1.23 is known to store filenames it cannot
            # translate to UTF-8 as raw strings (unfortunately without a
            # hdrcharset=BINARY header).
            # We first try the strict standard encoding, and if that fails we
            # fall back on the user's encoding and error handler.
            keyword = self._decode_pax_field(raw_keyword, "utf-8", "utf-8",
                    tarfile.errors)
            if keyword in PAX_NAME_FIELDS:
                value = self._decode_pax_field(raw_value, encoding, tarfile.encoding,
                        tarfile.errors)
            else:
                value = self._decode_pax_field(raw_value, "utf-8", "utf-8",
                        tarfile.errors)

            pax_headers[keyword] = value

        # Fetch the next header.
        try:
            next = self._fromtarfile(tarfile, dircheck=False)
        except HeaderError as e:
            raise SubsequentHeaderError(str(e)) from None

        # Process GNU sparse information.
        if "GNU.sparse.map" in pax_headers:
            # GNU extended sparse format version 0.1.
            self._proc_gnusparse_01(next, pax_headers)

        elif "GNU.sparse.size" in pax_headers:
            # GNU extended sparse format version 0.0.
            self._proc_gnusparse_00(next, raw_headers)

        elif pax_headers.get("GNU.sparse.major") == "1" and pax_headers.get("GNU.sparse.minor") == "0":
            # GNU extended sparse format version 1.0.
            self._proc_gnusparse_10(next, pax_headers, tarfile)

        if self.type in (XHDTYPE, SOLARIS_XHDTYPE):
            # Patch the TarInfo object with the extended header info.
            next._apply_pax_info(pax_headers, tarfile.encoding, tarfile.errors)
            next.offset = self.offset

            if "size" in pax_headers:
                # If the extended header replaces the size field,
                # we need to recalculate the offset where the next
                # header starts.
                offset = next.offset_data
                if next.isreg() or next.type not in SUPPORTED_TYPES:
                    offset += next._block(next.size)
                tarfile.offset = offset

        return next