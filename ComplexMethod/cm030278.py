def uu_decode(input, errors='strict'):
    assert errors == 'strict'
    infile = BytesIO(input)
    outfile = BytesIO()
    readline = infile.readline
    write = outfile.write

    # Find start of encoded data
    while 1:
        s = readline()
        if not s:
            raise ValueError('Missing "begin" line in input data')
        if s[:5] == b'begin':
            break

    # Decode
    while True:
        s = readline()
        if not s or s == b'end\n':
            break
        try:
            data = binascii.a2b_uu(s)
        except binascii.Error:
            # Workaround for broken uuencoders by /Fredrik Lundh
            nbytes = (((s[0]-32) & 63) * 4 + 5) // 3
            data = binascii.a2b_uu(s[:nbytes])
            #sys.stderr.write("Warning: %s\n" % str(v))
        write(data)
    if not s:
        raise ValueError('Truncated input data')

    return (outfile.getvalue(), len(input))