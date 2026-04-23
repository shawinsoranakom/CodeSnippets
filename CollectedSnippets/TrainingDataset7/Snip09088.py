def b62_encode(s):
    if s == 0:
        return "0"
    sign = "-" if s < 0 else ""
    s = abs(s)
    encoded = ""
    while s > 0:
        s, remainder = divmod(s, 62)
        encoded = BASE62_ALPHABET[remainder] + encoded
    return sign + encoded