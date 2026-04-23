def _separate(expr, delim=',', max_split=None):
        OP_CHARS = '+-*/%&|^=<>!,;{}:['
        if not expr:
            return
        counters = dict.fromkeys(_MATCHING_PARENS.values(), 0)
        start, splits, pos, delim_len = 0, 0, 0, len(delim) - 1
        in_quote, escaping, after_op, in_regex_char_group = None, False, True, False
        for idx, char in enumerate(expr):
            if not in_quote and char in _MATCHING_PARENS:
                counters[_MATCHING_PARENS[char]] += 1
            elif not in_quote and char in counters:
                # Something's wrong if we get negative, but ignore it anyway
                if counters[char]:
                    counters[char] -= 1
            elif not escaping:
                if char in _QUOTES and in_quote in (char, None):
                    if in_quote or after_op or char != '/':
                        in_quote = None if in_quote and not in_regex_char_group else char
                elif in_quote == '/' and char in '[]':
                    in_regex_char_group = char == '['
            escaping = not escaping and in_quote and char == '\\'
            in_unary_op = (not in_quote and not in_regex_char_group
                           and after_op not in (True, False) and char in '-+')
            after_op = char if (not in_quote and char in OP_CHARS) else (char.isspace() and after_op)

            if char != delim[pos] or any(counters.values()) or in_quote or in_unary_op:
                pos = 0
                continue
            elif pos != delim_len:
                pos += 1
                continue
            yield expr[start: idx - delim_len]
            start, pos = idx + 1, 0
            splits += 1
            if max_split and splits >= max_split:
                break
        yield expr[start:]