def parse_template(source, pattern):
    # parse 're' replacement string into list of literals and
    # group references
    s = Tokenizer(source)
    sget = s.get
    result = []
    literal = []
    lappend = literal.append
    def addliteral():
        if s.istext:
            result.append(''.join(literal))
        else:
            # The tokenizer implicitly decodes bytes objects as latin-1, we must
            # therefore re-encode the final representation.
            result.append(''.join(literal).encode('latin-1'))
        del literal[:]
    def addgroup(index, pos):
        if index > pattern.groups:
            raise s.error("invalid group reference %d" % index, pos)
        addliteral()
        result.append(index)
    groupindex = pattern.groupindex
    while True:
        this = sget()
        if this is None:
            break # end of replacement string
        if this[0] == "\\":
            # group
            c = this[1]
            if c == "g":
                if not s.match("<"):
                    raise s.error("missing <")
                name = s.getuntil(">", "group name")
                if not (name.isdecimal() and name.isascii()):
                    s.checkgroupname(name, 1)
                    try:
                        index = groupindex[name]
                    except KeyError:
                        raise IndexError("unknown group name %r" % name) from None
                else:
                    index = int(name)
                    if index >= MAXGROUPS:
                        raise s.error("invalid group reference %d" % index,
                                      len(name) + 1)
                addgroup(index, len(name) + 1)
            elif c == "0":
                if s.next in OCTDIGITS:
                    this += sget()
                    if s.next in OCTDIGITS:
                        this += sget()
                lappend(chr(int(this[1:], 8) & 0xff))
            elif c in DIGITS:
                isoctal = False
                if s.next in DIGITS:
                    this += sget()
                    if (c in OCTDIGITS and this[2] in OCTDIGITS and
                        s.next in OCTDIGITS):
                        this += sget()
                        isoctal = True
                        c = int(this[1:], 8)
                        if c > 0o377:
                            raise s.error('octal escape value %s outside of '
                                          'range 0-0o377' % this, len(this))
                        lappend(chr(c))
                if not isoctal:
                    addgroup(int(this[1:]), len(this) - 1)
            else:
                try:
                    this = chr(ESCAPES[this][1])
                except KeyError:
                    if c in ASCIILETTERS:
                        raise s.error('bad escape %s' % this, len(this)) from None
                lappend(this)
        else:
            lappend(this)
    addliteral()
    return result