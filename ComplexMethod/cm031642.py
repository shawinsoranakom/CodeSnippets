def write_repr(self, out, visited):
        # Write this out as a Python str literal

        # Get a PyUnicodeObject* within the Python gdb process:
        proxy = self.proxyval(visited)

        # Transliteration of Python's Object/unicodeobject.c:unicode_repr
        # to Python:
        if "'" in proxy and '"' not in proxy:
            quote = '"'
        else:
            quote = "'"
        out.write(quote)

        i = 0
        while i < len(proxy):
            ch = proxy[i]
            i += 1

            # Escape quotes and backslashes
            if ch == quote or ch == '\\':
                out.write('\\')
                out.write(ch)

            #  Map special whitespace to '\t', \n', '\r'
            elif ch == '\t':
                out.write('\\t')
            elif ch == '\n':
                out.write('\\n')
            elif ch == '\r':
                out.write('\\r')

            # Map non-printable US ASCII to '\xhh' */
            elif ch < ' ' or ord(ch) == 0x7F:
                out.write('\\x')
                out.write(hexdigits[(ord(ch) >> 4) & 0x000F])
                out.write(hexdigits[ord(ch) & 0x000F])

            # Copy ASCII characters as-is
            elif ord(ch) < 0x7F:
                out.write(ch)

            # Non-ASCII characters
            else:
                ucs = ch
                ch2 = None

                printable = ucs.isprintable()
                if printable:
                    try:
                        ucs.encode(ENCODING)
                    except UnicodeEncodeError:
                        printable = False

                # Map Unicode whitespace and control characters
                # (categories Z* and C* except ASCII space)
                if not printable:
                    if ch2 is not None:
                        # Match Python's representation of non-printable
                        # wide characters.
                        code = (ord(ch) & 0x03FF) << 10
                        code |= ord(ch2) & 0x03FF
                        code += 0x00010000
                    else:
                        code = ord(ucs)

                    # Map 8-bit characters to '\\xhh'
                    if code <= 0xff:
                        out.write('\\x')
                        out.write(hexdigits[(code >> 4) & 0x000F])
                        out.write(hexdigits[code & 0x000F])
                    # Map 21-bit characters to '\U00xxxxxx'
                    elif code >= 0x10000:
                        out.write('\\U')
                        out.write(hexdigits[(code >> 28) & 0x0000000F])
                        out.write(hexdigits[(code >> 24) & 0x0000000F])
                        out.write(hexdigits[(code >> 20) & 0x0000000F])
                        out.write(hexdigits[(code >> 16) & 0x0000000F])
                        out.write(hexdigits[(code >> 12) & 0x0000000F])
                        out.write(hexdigits[(code >> 8) & 0x0000000F])
                        out.write(hexdigits[(code >> 4) & 0x0000000F])
                        out.write(hexdigits[code & 0x0000000F])
                    # Map 16-bit characters to '\uxxxx'
                    else:
                        out.write('\\u')
                        out.write(hexdigits[(code >> 12) & 0x000F])
                        out.write(hexdigits[(code >> 8) & 0x000F])
                        out.write(hexdigits[(code >> 4) & 0x000F])
                        out.write(hexdigits[code & 0x000F])
                else:
                    # Copy characters as-is
                    out.write(ch)
                    if ch2 is not None:
                        out.write(ch2)

        out.write(quote)