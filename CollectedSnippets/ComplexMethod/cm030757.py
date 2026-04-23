def native_type_range(fmt):
    """Return range of a native type."""
    if fmt == 'c':
        lh = (0, 256)
    elif fmt == '?':
        lh = (0, 2)
    elif fmt == 'e':
        lh = (-65519, 65520)
    elif fmt == 'f':
        lh = (-(1<<63), 1<<63)
    elif fmt == 'd':
        lh = (-(1<<1023), 1<<1023)
    elif fmt == 'F':
        lh = (-(1<<63), 1<<63)
    elif fmt == 'D':
        lh = (-(1<<1023), 1<<1023)
    else:
        for exp in (128, 127, 64, 63, 32, 31, 16, 15, 8, 7):
            try:
                struct.pack(fmt, (1<<exp)-1)
                break
            except struct.error:
                pass
        lh = (-(1<<exp), 1<<exp) if exp & 1 else (0, 1<<exp)
    return lh