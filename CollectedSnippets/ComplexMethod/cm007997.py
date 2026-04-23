def parse(cls, parser):
        parser = parser.child()

        id_ = None
        m = parser.consume(cls._REGEX_ID)
        if m:
            id_ = m.group(1)

        m0 = parser.consume(_REGEX_TS)
        if not m0:
            return None
        if not parser.consume(cls._REGEX_ARROW):
            return None
        m1 = parser.consume(_REGEX_TS)
        if not m1:
            return None
        m2 = parser.consume(cls._REGEX_SETTINGS)
        parser.consume(_REGEX_OPTIONAL_WHITESPACE)
        if not parser.consume(_REGEX_NL):
            return None

        start = _parse_ts(m0)
        end = _parse_ts(m1)
        settings = m2.group(1) if m2 is not None else None

        text = io.StringIO()
        while True:
            m = parser.consume(cls._REGEX_PAYLOAD)
            if not m:
                break
            text.write(m.group(0))

        parser.commit()
        return cls(
            id=id_,
            start=start, end=end, settings=settings,
            text=text.getvalue(),
        )