def readmap(filename):

    with open(filename) as f:
        lines = f.readlines()
    enc2uni = {}
    identity = []
    unmapped = list(range(256))

    # UTC mapping tables per convention don't include the identity
    # mappings for code points 0x00 - 0x1F and 0x7F, unless these are
    # explicitly mapped to different characters or undefined
    for i in list(range(32)) + [127]:
        identity.append(i)
        unmapped.remove(i)
        enc2uni[i] = (i, 'CONTROL CHARACTER')

    for line in lines:
        line = line.strip()
        if not line or line[0] == '#':
            continue
        m = mapRE.match(line)
        if not m:
            #print '* not matched: %s' % repr(line)
            continue
        enc,uni,comment = m.groups()
        enc = parsecodes(enc)
        uni = parsecodes(uni)
        if comment is None:
            comment = ''
        else:
            comment = comment[1:].strip()
        if not isinstance(enc, tuple) and enc < 256:
            if enc in unmapped:
                unmapped.remove(enc)
            if enc == uni:
                identity.append(enc)
            enc2uni[enc] = (uni,comment)
        else:
            enc2uni[enc] = (uni,comment)

    # If there are more identity-mapped entries than unmapped entries,
    # it pays to generate an identity dictionary first, and add explicit
    # mappings to None for the rest
    if len(identity) >= len(unmapped):
        for enc in unmapped:
            enc2uni[enc] = (MISSING_CODE, "")
        enc2uni['IDENTITY'] = 256

    return enc2uni