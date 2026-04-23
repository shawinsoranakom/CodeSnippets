def _buffer_decode(self, input, errors, final):
        if errors != 'strict':
            raise UnicodeError(f"Unsupported error handling: {errors}")

        if not input:
            return ("", 0)

        # IDNA allows decoding to operate on Unicode strings, too.
        if isinstance(input, str):
            labels = dots.split(input)
        else:
            # Must be ASCII string
            try:
                input = str(input, "ascii")
            except (UnicodeEncodeError, UnicodeDecodeError) as exc:
                raise UnicodeDecodeError("idna", input,
                                         exc.start, exc.end, exc.reason)
            labels = input.split(".")

        trailing_dot = ''
        if labels:
            if not labels[-1]:
                trailing_dot = '.'
                del labels[-1]
            elif not final:
                # Keep potentially unfinished label until the next call
                del labels[-1]
                if labels:
                    trailing_dot = '.'

        result = []
        size = 0
        for label in labels:
            try:
                u_label = ToUnicode(label)
            except (UnicodeEncodeError, UnicodeDecodeError) as exc:
                raise UnicodeDecodeError(
                    "idna",
                    input.encode("ascii", errors="backslashreplace"),
                    size + exc.start,
                    size + exc.end,
                    exc.reason,
                )
            else:
                result.append(u_label)
            if size:
                size += 1
            size += len(label)

        result = ".".join(result) + trailing_dot
        size += len(trailing_dot)
        return (result, size)