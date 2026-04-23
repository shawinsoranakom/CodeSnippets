def parse_fragment(frag_content):
    """
    A generator that yields (partially) parsed WebVTT blocks when given
    a bytes object containing the raw contents of a WebVTT file.
    """

    parser = _MatchParser(frag_content.decode())

    yield Magic.parse(parser)

    while not parser.match(_REGEX_EOF):
        if parser.consume(_REGEX_BLANK):
            continue

        block = RegionBlock.parse(parser)
        if block:
            yield block
            continue
        block = StyleBlock.parse(parser)
        if block:
            yield block
            continue
        block = CommentBlock.parse(parser)
        if block:
            yield block  # XXX: or skip
            continue

        break

    while not parser.match(_REGEX_EOF):
        if parser.consume(_REGEX_BLANK):
            continue

        block = CommentBlock.parse(parser)
        if block:
            yield block  # XXX: or skip
            continue
        block = CueBlock.parse(parser)
        if block:
            yield block
            continue

        raise ParseError(parser)