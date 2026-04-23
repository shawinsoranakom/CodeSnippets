def _remove_unused_ops(tokens):
            # Remove operators that we don't use and join them with the surrounding strings.
            # E.g. 'mp4' '-' 'baseline' '-' '16x9' is converted to 'mp4-baseline-16x9'
            ALLOWED_OPS = ('/', '+', ',', '(', ')')
            last_string, last_start, last_end, last_line = None, None, None, None
            for type_, string_, start, end, line in tokens:
                if type_ == tokenize.OP and string_ == '[':
                    if last_string:
                        yield tokenize.NAME, last_string, last_start, last_end, last_line
                        last_string = None
                    yield type_, string_, start, end, line
                    # everything inside brackets will be handled by _parse_filter
                    for type_, string_, start, end, line in tokens:
                        yield type_, string_, start, end, line
                        if type_ == tokenize.OP and string_ == ']':
                            break
                elif type_ == tokenize.OP and string_ in ALLOWED_OPS:
                    if last_string:
                        yield tokenize.NAME, last_string, last_start, last_end, last_line
                        last_string = None
                    yield type_, string_, start, end, line
                elif type_ in [tokenize.NAME, tokenize.NUMBER, tokenize.OP]:
                    if not last_string:
                        last_string = string_
                        last_start = start
                        last_end = end
                    else:
                        last_string += string_
            if last_string:
                yield tokenize.NAME, last_string, last_start, last_end, last_line