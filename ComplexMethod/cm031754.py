def make(filename, outfile):
    ID = 1
    STR = 2
    CTXT = 3

    # Compute .mo name from .po name and arguments
    if filename.endswith('.po'):
        infile = filename
    else:
        infile = filename + '.po'
    if outfile is None:
        outfile = os.path.splitext(infile)[0] + '.mo'

    try:
        with open(infile, 'rb') as f:
            lines = f.readlines()
    except OSError as msg:
        print(msg, file=sys.stderr)
        sys.exit(1)

    if lines[0].startswith(codecs.BOM_UTF8):
        print(
            f"The file {infile} starts with a UTF-8 BOM which is not allowed in .po files.\n"
            "Please save the file without a BOM and try again.",
            file=sys.stderr
        )
        sys.exit(1)

    section = msgctxt = None
    msgid = msgstr = b''
    fuzzy = 0

    # Start off assuming Latin-1, so everything decodes without failure,
    # until we know the exact encoding
    encoding = 'latin-1'

    # Parse the catalog
    lno = 0
    for l in lines:
        l = l.decode(encoding)
        lno += 1
        # If we get a comment line after a msgstr, this is a new entry
        if l[0] == '#' and section == STR:
            add(msgctxt, msgid, msgstr, fuzzy)
            section = msgctxt = None
            fuzzy = 0
        # Record a fuzzy mark
        if l[:2] == '#,' and 'fuzzy' in l:
            fuzzy = 1
        # Skip comments
        if l[0] == '#':
            continue
        # Now we are in a msgid or msgctxt section, output previous section
        if l.startswith('msgctxt'):
            if section == STR:
                add(msgctxt, msgid, msgstr, fuzzy)
            section = CTXT
            l = l[7:]
            msgctxt = b''
        elif l.startswith('msgid') and not l.startswith('msgid_plural'):
            if section == STR:
                if not msgid:
                    # Filter out POT-Creation-Date
                    # See issue #131852
                    msgstr = b''.join(line for line in msgstr.splitlines(True)
                                      if not line.startswith(b'POT-Creation-Date:'))

                    # See whether there is an encoding declaration
                    p = HeaderParser()
                    charset = p.parsestr(msgstr.decode(encoding)).get_content_charset()
                    if charset:
                        encoding = charset
                add(msgctxt, msgid, msgstr, fuzzy)
                msgctxt = None
            section = ID
            l = l[5:]
            msgid = msgstr = b''
            is_plural = False
        # This is a message with plural forms
        elif l.startswith('msgid_plural'):
            if section != ID:
                print(f'msgid_plural not preceded by msgid on {infile}:{lno}',
                      file=sys.stderr)
                sys.exit(1)
            l = l[12:]
            msgid += b'\0' # separator of singular and plural
            is_plural = True
        # Now we are in a msgstr section
        elif l.startswith('msgstr'):
            section = STR
            if l.startswith('msgstr['):
                if not is_plural:
                    print(f'plural without msgid_plural on {infile}:{lno}',
                          file=sys.stderr)
                    sys.exit(1)
                l = l.split(']', 1)[1]
                if msgstr:
                    msgstr += b'\0' # Separator of the various plural forms
            else:
                if is_plural:
                    print(f'indexed msgstr required for plural on {infile}:{lno}',
                          file=sys.stderr)
                    sys.exit(1)
                l = l[6:]
        # Skip empty lines
        l = l.strip()
        if not l:
            continue
        l = ast.literal_eval(l)
        if section == CTXT:
            msgctxt += l.encode(encoding)
        elif section == ID:
            msgid += l.encode(encoding)
        elif section == STR:
            msgstr += l.encode(encoding)
        else:
            print(f'Syntax error on {infile}:{lno} before:', file=sys.stderr)
            print(l, file=sys.stderr)
            sys.exit(1)
    # Add last entry
    if section == STR:
        add(msgctxt, msgid, msgstr, fuzzy)

    # Compute output
    output = generate()

    try:
        with open(outfile,"wb") as f:
            f.write(output)
    except OSError as msg:
        print(msg, file=sys.stderr)