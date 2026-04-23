def decode_generalized_number(extended, extpos, bias, errors):
    """3.3 Generalized variable-length integers"""
    result = 0
    w = 1
    j = 0
    while 1:
        try:
            char = extended[extpos]
        except IndexError:
            if errors == "strict":
                raise UnicodeDecodeError("punycode", extended, extpos, extpos+1,
                                         "incomplete punycode string")
            return extpos + 1, None
        extpos += 1
        if 0x41 <= char <= 0x5A: # A-Z
            digit = char - 0x41
        elif 0x30 <= char <= 0x39:
            digit = char - 22 # 0x30-26
        elif errors == "strict":
            raise UnicodeDecodeError("punycode", extended, extpos-1, extpos,
                                     f"Invalid extended code point '{extended[extpos-1]}'")
        else:
            return extpos, None
        t = T(j, bias)
        result += digit * w
        if digit < t:
            return extpos, result
        w = w * (36 - t)
        j += 1