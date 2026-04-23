def decode(input, output, header=False):
    """Read 'input', apply quoted-printable decoding, and write to 'output'.
    'input' and 'output' are binary file objects.
    If 'header' is true, decode underscore as space (per RFC 1522)."""

    if a2b_qp is not None:
        data = input.read()
        odata = a2b_qp(data, header=header)
        output.write(odata)
        return

    new = b''
    while line := input.readline():
        i, n = 0, len(line)
        if n > 0 and line[n-1:n] == b'\n':
            partial = 0; n = n-1
            # Strip trailing whitespace
            while n > 0 and line[n-1:n] in b" \t\r":
                n = n-1
        else:
            partial = 1
        while i < n:
            c = line[i:i+1]
            if c == b'_' and header:
                new = new + b' '; i = i+1
            elif c != ESCAPE:
                new = new + c; i = i+1
            elif i+1 == n and not partial:
                partial = 1; break
            elif i+1 < n and line[i+1:i+2] == ESCAPE:
                new = new + ESCAPE; i = i+2
            elif i+2 < n and ishex(line[i+1:i+2]) and ishex(line[i+2:i+3]):
                new = new + bytes((unhex(line[i+1:i+3]),)); i = i+3
            else: # Bad escape sequence -- leave it in
                new = new + c; i = i+1
        if not partial:
            output.write(new + b'\n')
            new = b''
    if new:
        output.write(new)