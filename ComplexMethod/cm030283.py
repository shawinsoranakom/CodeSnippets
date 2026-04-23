def decode(self, input, errors='strict'):

        if errors != 'strict':
            raise UnicodeError(f"Unsupported error handling: {errors}")

        if not input:
            return "", 0

        # IDNA allows decoding to operate on Unicode strings, too.
        if not isinstance(input, bytes):
            # XXX obviously wrong, see #3232
            input = bytes(input)

        if ace_prefix not in input.lower():
            # Fast path
            try:
                return input.decode('ascii'), len(input)
            except UnicodeDecodeError:
                pass

        labels = input.split(b".")

        if labels and len(labels[-1]) == 0:
            trailing_dot = '.'
            del labels[-1]
        else:
            trailing_dot = ''

        result = []
        for i, label in enumerate(labels):
            try:
                u_label = ToUnicode(label)
            except (UnicodeEncodeError, UnicodeDecodeError) as exc:
                offset = sum(len(x) for x in labels[:i]) + len(labels[:i])
                raise UnicodeDecodeError(
                    "idna", input, offset+exc.start, offset+exc.end, exc.reason)
            else:
                result.append(u_label)

        return ".".join(result)+trailing_dot, len(input)