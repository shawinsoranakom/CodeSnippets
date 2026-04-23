def _replace_charref(s):
    s = s.group(1)
    if s[0] == '#':
        # numeric charref
        if s[1] in 'xX':
            num = int(s[2:].rstrip(';'), 16)
        else:
            num = int(s[1:].rstrip(';'))
        if num in _invalid_charrefs:
            return _invalid_charrefs[num]
        if 0xD800 <= num <= 0xDFFF or num > 0x10FFFF:
            return '\uFFFD'
        if num in _invalid_codepoints:
            return ''
        return chr(num)
    else:
        # named charref
        if s in _html5:
            return _html5[s]
        # find the longest matching name (as defined by the standard)
        for x in range(len(s)-1, 1, -1):
            if s[:x] in _html5:
                return _html5[s[:x]] + s[x:]
        else:
            return '&' + s