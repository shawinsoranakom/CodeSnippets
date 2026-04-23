def _remove_unused_ops(tokens):
            # Remove operators that we don't use and join them with the surrounding strings
            # for example: 'mp4' '-' 'baseline' '-' '16x9' is converted to 'mp4-baseline-16x9'
            ALLOWED_OPS = ('/', '+', ',', '(', ')')
            last_string, last_start, last_end, last_line = None, None, None, None
            for type, string, start, end, line in tokens:
                if type == tokenize.OP and string == '[':
                    if last_string:
                        yield tokenize.NAME, last_string, last_start, last_end, last_line
                        last_string = None
                    yield type, string, start, end, line
                    # everything inside brackets will be handled by _parse_filter
                    for type, string, start, end, line in tokens:
                        yield type, string, start, end, line
                        if type == tokenize.OP and string == ']':
                            break
                elif type == tokenize.OP and string in ALLOWED_OPS:
                    if last_string:
                        yield tokenize.NAME, last_string, last_start, last_end, last_line
                        last_string = None
                    yield type, string, start, end, line
                elif type in [tokenize.NAME, tokenize.NUMBER, tokenize.OP]:
                    if not last_string:
                        last_string = string
                        last_start = start
                        last_end = end
                    else:
                        last_string += string
            if last_string:
                yield tokenize.NAME, last_string, last_start, last_end, last_line