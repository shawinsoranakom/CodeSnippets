def is_soft_keyword_used(*tokens: TI | None) -> bool:
    """Returns True if the current token is a keyword in this context.

    For the `*tokens` to match anything, they have to be a three-tuple of
    (previous, current, next).
    """
    trace("is_soft_keyword_used{t}", t=tokens)
    match tokens:
        case (
            None | TI(T.NEWLINE) | TI(T.INDENT) | TI(string=":"),
            TI(string="match"),
            TI(T.NUMBER | T.STRING | T.FSTRING_START | T.TSTRING_START)
            | TI(T.OP, string="(" | "*" | "[" | "{" | "~" | "...")
        ):
            return True
        case (
            None | TI(T.NEWLINE) | TI(T.INDENT) | TI(string=":"),
            TI(string="match"),
            TI(T.NAME, string=s)
        ):
            if keyword.iskeyword(s):
                return s in keyword_first_sets_match
            return True
        case (
            None | TI(T.NEWLINE) | TI(T.INDENT) | TI(T.DEDENT) | TI(string=":"),
            TI(string="case"),
            TI(T.NUMBER | T.STRING | T.FSTRING_START | T.TSTRING_START)
            | TI(T.OP, string="(" | "*" | "-" | "[" | "{")
        ):
            return True
        case (
            None | TI(T.NEWLINE) | TI(T.INDENT) | TI(T.DEDENT) | TI(string=":"),
            TI(string="case"),
            TI(T.NAME, string=s)
        ):
            if keyword.iskeyword(s):
                return s in keyword_first_sets_case
            return True
        case (TI(string="case"), TI(string="_"), TI(string=":")):
            return True
        case (
            None | TI(T.NEWLINE) | TI(T.INDENT) | TI(T.DEDENT) | TI(string=":"),
            TI(string="type"),
            TI(T.NAME, string=s)
        ):
            return not keyword.iskeyword(s)
        case (
            None | TI(T.NEWLINE) | TI(T.INDENT) | TI(T.DEDENT) | TI(string=":" | ";"),
            TI(string="lazy"),
            TI(string="import") | TI(string="from")
        ):
            return True
        case _:
            return False