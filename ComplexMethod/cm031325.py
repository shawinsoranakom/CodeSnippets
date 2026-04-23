def gen_colors_from_token_stream(
    token_generator: Iterator[TI],
    line_lengths: list[int],
) -> Iterator[ColorSpan]:
    token_window = prev_next_window(token_generator)

    is_def_name = False
    bracket_level = 0
    for prev_token, token, next_token in token_window:
        assert token is not None
        if token.start == token.end:
            continue

        match token.type:
            case (
                T.STRING
                | T.FSTRING_START | T.FSTRING_MIDDLE | T.FSTRING_END
                | T.TSTRING_START | T.TSTRING_MIDDLE | T.TSTRING_END
            ):
                span = Span.from_token(token, line_lengths)
                yield ColorSpan(span, "string")
            case T.COMMENT:
                span = Span.from_token(token, line_lengths)
                yield ColorSpan(span, "comment")
            case T.NUMBER:
                span = Span.from_token(token, line_lengths)
                yield ColorSpan(span, "number")
            case T.OP:
                if token.string in "([{":
                    bracket_level += 1
                elif token.string in ")]}":
                    bracket_level -= 1
                span = Span.from_token(token, line_lengths)
                yield ColorSpan(span, "op")
            case T.NAME:
                if is_def_name:
                    is_def_name = False
                    span = Span.from_token(token, line_lengths)
                    yield ColorSpan(span, "definition")
                elif keyword.iskeyword(token.string):
                    span_cls = "keyword"
                    if token.string in KEYWORD_CONSTANTS:
                        span_cls = "keyword_constant"
                    span = Span.from_token(token, line_lengths)
                    yield ColorSpan(span, span_cls)
                    if token.string in IDENTIFIERS_AFTER:
                        is_def_name = True
                elif (
                    keyword.issoftkeyword(token.string)
                    and bracket_level == 0
                    and is_soft_keyword_used(prev_token, token, next_token)
                ):
                    span = Span.from_token(token, line_lengths)
                    yield ColorSpan(span, "soft_keyword")
                elif (
                    token.string in BUILTINS
                    and not (prev_token and prev_token.exact_type == T.DOT)
                ):
                    span = Span.from_token(token, line_lengths)
                    yield ColorSpan(span, "builtin")