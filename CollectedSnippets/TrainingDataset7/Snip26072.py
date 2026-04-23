def rfc2047_decode(s):
        # Decode using legacy decode_header() (which doesn't have the bug).
        return "".join(
            (
                segment
                if charset is None and isinstance(segment, str)
                else segment.decode(charset or "ascii")
            )
            for segment, charset in decode_header(s)
        )