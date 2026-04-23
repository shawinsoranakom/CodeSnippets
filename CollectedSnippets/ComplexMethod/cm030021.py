def create_pax_header(self, info, encoding):
        """Return the object as a ustar header block. If it cannot be
           represented this way, prepend a pax extended header sequence
           with supplement information.
        """
        info["magic"] = POSIX_MAGIC
        pax_headers = self.pax_headers.copy()

        # Test string fields for values that exceed the field length or cannot
        # be represented in ASCII encoding.
        for name, hname, length in (
                ("name", "path", LENGTH_NAME), ("linkname", "linkpath", LENGTH_LINK),
                ("uname", "uname", 32), ("gname", "gname", 32)):

            if hname in pax_headers:
                # The pax header has priority.
                continue

            # Try to encode the string as ASCII.
            try:
                info[name].encode("ascii", "strict")
            except UnicodeEncodeError:
                pax_headers[hname] = info[name]
                continue

            if len(info[name]) > length:
                pax_headers[hname] = info[name]

        # Test number fields for values that exceed the field limit or values
        # that like to be stored as float.
        for name, digits in (("uid", 8), ("gid", 8), ("size", 12), ("mtime", 12)):
            needs_pax = False

            val = info[name]
            val_is_float = isinstance(val, float)
            val_int = round(val) if val_is_float else val
            if not 0 <= val_int < 8 ** (digits - 1):
                # Avoid overflow.
                info[name] = 0
                needs_pax = True
            elif val_is_float:
                # Put rounded value in ustar header, and full
                # precision value in pax header.
                info[name] = val_int
                needs_pax = True

            # The existing pax header has priority.
            if needs_pax and name not in pax_headers:
                pax_headers[name] = str(val)

        # Create a pax extended header if necessary.
        if pax_headers:
            buf = self._create_pax_generic_header(pax_headers, XHDTYPE, encoding)
        else:
            buf = b""

        return buf + self._create_header(info, USTAR_FORMAT, "ascii", "replace")