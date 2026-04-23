def build_like_regex(value: str, exact: bool):
                yield '^' if exact else '.*'
                escaped = False
                for char in value:
                    if escaped:
                        escaped = False
                        yield re.escape(char)
                    elif char == '\\':
                        escaped = True
                    elif char == '%':
                        yield '.*'
                    elif char == '_':
                        yield '.'
                    else:
                        yield re.escape(char)
                if exact:
                    yield '$'