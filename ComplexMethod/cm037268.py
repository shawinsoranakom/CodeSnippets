def _prefix_needs_context(parsed) -> bool:
    """Return True if there's a look-around/anchor before any consumer."""

    def subpattern_consumes(parsed) -> bool:
        """Return True if subpattern can consume at least one character."""
        tokens = parsed.data if hasattr(parsed, "data") else parsed
        for ttype, tval in tokens:
            # literal, character class, or dot always consumes
            if ttype in (sre_parse.LITERAL, sre_parse.IN, sre_parse.ANY):
                return True
            # quantified subpattern: check inner pattern
            elif ttype == sre_parse.MAX_REPEAT:
                _, mx, sub = tval
                if mx != 0 and subpattern_consumes(sub):
                    return True
            # alternation: if any branch consumes, the whole does
            elif ttype == sre_parse.BRANCH:
                _, branches = tval
                if any(subpattern_consumes(br) for br in branches):
                    return True
            # grouped subpattern: recurse into its contents
            elif ttype == sre_parse.SUBPATTERN and subpattern_consumes(tval[3]):
                return True
        # No consumers, return False
        return False

    tokens = parsed.data if hasattr(parsed, "data") else parsed
    for ttype, tval in tokens:
        # Direct anchors or look-around
        if ttype == sre_parse.AT or ttype in (
            sre_constants.ASSERT,
            sre_constants.ASSERT_NOT,
        ):
            return True

        # Nested subpattern: check
        if ttype == sre_parse.SUBPATTERN:
            # tval: (group, add_flags, del_flags, subpattern)
            if _prefix_needs_context(tval[3]):
                return True
            if subpattern_consumes(tval[3]):
                return False

        # if any branch has a prefix anchor => True,
        # else if at least one branch consumes => prefix ends => False
        elif ttype == sre_parse.BRANCH:
            saw_consumer = False
            for br in tval[1]:
                if _prefix_needs_context(br):
                    return True
                if subpattern_consumes(br):
                    saw_consumer = True
            if saw_consumer:
                return False

        # Immediate consumer tokens
        elif ttype in (sre_parse.LITERAL, sre_parse.IN, sre_parse.ANY):
            return False

        # if subpattern has anchor => True, if it can consume => stop
        elif ttype == sre_parse.MAX_REPEAT:
            if _prefix_needs_context(tval[2]):
                return True
            if subpattern_consumes(tval[2]):
                return False

    return False