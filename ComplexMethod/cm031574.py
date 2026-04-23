def quote_from_bytes(bs, safe='/'):
    """Like quote(), but accepts a bytes object rather than a str, and does
    not perform string-to-bytes encoding.  It always returns an ASCII string.
    quote_from_bytes(b'abc def\x3f') -> 'abc%20def%3f'
    """
    if not isinstance(bs, (bytes, bytearray)):
        raise TypeError("quote_from_bytes() expected bytes")
    if not bs:
        return ''
    if isinstance(safe, str):
        # Normalize 'safe' by converting to bytes and removing non-ASCII chars
        safe = safe.encode('ascii', 'ignore')
    else:
        # List comprehensions are faster than generator expressions.
        safe = bytes([c for c in safe if c < 128])
    if not bs.rstrip(_ALWAYS_SAFE_BYTES + safe):
        return bs.decode()
    quoter = _byte_quoter_factory(safe)
    if (bs_len := len(bs)) < 200_000:
        return ''.join(map(quoter, bs))
    else:
        # This saves memory - https://github.com/python/cpython/issues/95865
        chunk_size = math.isqrt(bs_len)
        chunks = [''.join(map(quoter, bs[i:i+chunk_size]))
                  for i in range(0, bs_len, chunk_size)]
        return ''.join(chunks)