def _separate(cls, expr, delim=',', max_split=None, skip_delims=None):
        if not expr:
            return
        # collections.Counter() is ~10% slower in both 2.7 and 3.9
        counters = dict((k, 0) for k in _MATCHING_PARENS.values())
        start, splits, pos, delim_len = 0, 0, 0, len(delim) - 1
        in_quote, escaping, after_op, in_regex_char_group = None, False, True, False
        skipping = 0
        if skip_delims:
            skip_delims = variadic(skip_delims)
        skip_txt = None
        for idx, char in enumerate(expr):
            if skip_txt and idx <= skip_txt[1]:
                continue
            paren_delta = 0
            if not in_quote:
                if char == '/' and expr[idx:idx + 2] == '/*':
                    # skip a comment
                    skip_txt = expr[idx:].find('*/', 2)
                    skip_txt = [idx, idx + skip_txt + 1] if skip_txt >= 2 else None
                    if skip_txt:
                        continue
                if char in _MATCHING_PARENS:
                    counters[_MATCHING_PARENS[char]] += 1
                    paren_delta = 1
                elif char in counters:
                    counters[char] -= 1
                    paren_delta = -1
            if not escaping:
                if char in _QUOTES and in_quote in (char, None):
                    if in_quote or after_op or char != '/':
                        in_quote = None if in_quote and not in_regex_char_group else char
                elif in_quote == '/' and char in '[]':
                    in_regex_char_group = char == '['
            escaping = not escaping and in_quote and char == '\\'
            after_op = not in_quote and (char in cls.OP_CHARS or paren_delta > 0 or (after_op and char.isspace()))

            if char != delim[pos] or any(counters.values()) or in_quote:
                pos = skipping = 0
                continue
            elif skipping > 0:
                skipping -= 1
                continue
            elif pos == 0 and skip_delims:
                here = expr[idx:]
                for s in skip_delims:
                    if here.startswith(s) and s:
                        skipping = len(s) - 1
                        break
                if skipping > 0:
                    continue
            if pos < delim_len:
                pos += 1
                continue
            if skip_txt and skip_txt[0] >= start and skip_txt[1] <= idx - delim_len:
                yield expr[start:skip_txt[0]] + expr[skip_txt[1] + 1: idx - delim_len]
            else:
                yield expr[start: idx - delim_len]
            skip_txt = None
            start, pos = idx + 1, 0
            splits += 1
            if max_split and splits >= max_split:
                break
        if skip_txt and skip_txt[0] >= start:
            yield expr[start:skip_txt[0]] + expr[skip_txt[1] + 1:]
        else:
            yield expr[start:]