def encode(self, input, errors='strict'):

        if errors != 'strict':
            # IDNA is quite clear that implementations must be strict
            raise UnicodeError(f"Unsupported error handling: {errors}")

        if not input:
            return b'', 0

        try:
            result = input.encode('ascii')
        except UnicodeEncodeError:
            pass
        else:
            # ASCII name: fast path
            labels = result.split(b'.')
            for i, label in enumerate(labels[:-1]):
                if len(label) == 0:
                    offset = sum(len(l) for l in labels[:i]) + i
                    raise UnicodeEncodeError("idna", input, offset, offset+1,
                                             "label empty")
            for i, label in enumerate(labels):
                if len(label) >= 64:
                    offset = sum(len(l) for l in labels[:i]) + i
                    raise UnicodeEncodeError("idna", input, offset, offset+len(label),
                                             "label too long")
            return result, len(input)

        result = bytearray()
        labels = dots.split(input)
        if labels and not labels[-1]:
            trailing_dot = b'.'
            del labels[-1]
        else:
            trailing_dot = b''
        for i, label in enumerate(labels):
            if result:
                # Join with U+002E
                result.extend(b'.')
            try:
                result.extend(ToASCII(label))
            except (UnicodeEncodeError, UnicodeDecodeError) as exc:
                offset = sum(len(l) for l in labels[:i]) + i
                raise UnicodeEncodeError(
                    "idna",
                    input,
                    offset + exc.start,
                    offset + exc.end,
                    exc.reason,
                )
        result += trailing_dot
        return result.take_bytes(), len(input)