def write_repr(self, out, visited):
        # Write this out as a Python bytes literal, i.e. with a "b" prefix

        # Get a PyStringObject* within the Python gdb process:
        proxy = self.proxyval(visited)

        # Transliteration of Python's Objects/bytesobject.c:PyBytes_Repr
        # to Python code:
        quote = "'"
        if "'" in proxy and not '"' in proxy:
            quote = '"'
        out.write('b')
        out.write(quote)
        for byte in proxy:
            if byte == quote or byte == '\\':
                out.write('\\')
                out.write(byte)
            elif byte == '\t':
                out.write('\\t')
            elif byte == '\n':
                out.write('\\n')
            elif byte == '\r':
                out.write('\\r')
            elif byte < ' ' or ord(byte) >= 0x7f:
                out.write('\\x')
                out.write(hexdigits[(ord(byte) & 0xf0) >> 4])
                out.write(hexdigits[ord(byte) & 0xf])
            else:
                out.write(byte)
        out.write(quote)