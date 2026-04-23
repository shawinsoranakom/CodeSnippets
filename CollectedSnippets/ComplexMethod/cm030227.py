def _process_tokens(tokens):
    INDENT = tokenize.INDENT
    DEDENT = tokenize.DEDENT
    NEWLINE = tokenize.NEWLINE
    JUNK = tokenize.COMMENT, tokenize.NL
    indents = [Whitespace("")]
    check_equal = 0

    for (type, token, start, end, line) in tokens:
        if type == NEWLINE:
            # a program statement, or ENDMARKER, will eventually follow,
            # after some (possibly empty) run of tokens of the form
            #     (NL | COMMENT)* (INDENT | DEDENT+)?
            # If an INDENT appears, setting check_equal is wrong, and will
            # be undone when we see the INDENT.
            check_equal = 1

        elif type == INDENT:
            check_equal = 0
            thisguy = Whitespace(token)
            if not indents[-1].less(thisguy):
                witness = indents[-1].not_less_witness(thisguy)
                msg = "indent not greater e.g. " + format_witnesses(witness)
                raise NannyNag(start[0], msg, line)
            indents.append(thisguy)

        elif type == DEDENT:
            # there's nothing we need to check here!  what's important is
            # that when the run of DEDENTs ends, the indentation of the
            # program statement (or ENDMARKER) that triggered the run is
            # equal to what's left at the top of the indents stack

            # Ouch!  This assert triggers if the last line of the source
            # is indented *and* lacks a newline -- then DEDENTs pop out
            # of thin air.
            # assert check_equal  # else no earlier NEWLINE, or an earlier INDENT
            check_equal = 1

            del indents[-1]

        elif check_equal and type not in JUNK:
            # this is the first "real token" following a NEWLINE, so it
            # must be the first token of the next program statement, or an
            # ENDMARKER; the "line" argument exposes the leading whitespace
            # for this statement; in the case of ENDMARKER, line is an empty
            # string, so will properly match the empty string with which the
            # "indents" stack was seeded
            check_equal = 0
            thisguy = Whitespace(line)
            if not indents[-1].equal(thisguy):
                witness = indents[-1].not_equal_witness(thisguy)
                msg = "indent not equal e.g. " + format_witnesses(witness)
                raise NannyNag(start[0], msg, line)