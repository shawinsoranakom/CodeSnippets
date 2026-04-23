def __parse_tsmap(cls, parser):
        parser = parser.child()

        while True:
            m = parser.consume(cls._REGEX_TSMAP_LOCAL)
            if m:
                m = parser.consume(_REGEX_TS)
                if m is None:
                    raise ParseError(parser)
                local = _parse_ts(m)
                if local is None:
                    raise ParseError(parser)
            else:
                m = parser.consume(cls._REGEX_TSMAP_MPEGTS)
                if m:
                    mpegts = int_or_none(m.group(1))
                    if mpegts is None:
                        raise ParseError(parser)
                else:
                    raise ParseError(parser)
            if parser.consume(cls._REGEX_TSMAP_SEP):
                continue
            if parser.consume(_REGEX_NL):
                break
            raise ParseError(parser)

        parser.commit()
        return local, mpegts