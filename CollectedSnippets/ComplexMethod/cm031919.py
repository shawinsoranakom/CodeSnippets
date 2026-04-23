def iter_builtin_types(filenames=None):
    decls = {}
    seen = set()
    for filename in iter_header_files():
        seen.add(filename)
        with open(filename) as infile:
            for lno, line in enumerate(infile, 1):
                decl = BuiltinTypeDecl.from_line(line, filename, lno)
                if not decl:
                    continue
                _ensure_decl(decl, decls)
    srcfiles = []
    for filename in iter_filenames():
        if filename.endswith('.c'):
            srcfiles.append(filename)
            continue
        if filename in seen:
            continue
        with open(filename) as infile:
            for lno, line in enumerate(infile, 1):
                decl = BuiltinTypeDecl.from_line(line, filename, lno)
                if not decl:
                    continue
                _ensure_decl(decl, decls)

    for filename in srcfiles:
        with open(filename) as infile:
            localdecls = {}
            for lno, line in enumerate(infile, 1):
                parsed = _parse_line(line)
                if not parsed:
                    continue
                name, isdecl, kind = parsed
                if isdecl:
                    decl = BuiltinTypeDecl.from_parsed(name, kind, filename, lno)
                    if not decl:
                        raise NotImplementedError((filename, line))
                    _ensure_decl(decl, localdecls)
                else:
                    builtin = BuiltinTypeInfo.from_parsed(
                            name, kind, filename, lno,
                            decls=decls if name in decls else localdecls)
                    if not builtin:
                        raise NotImplementedError((filename, line))
                    yield builtin