def analyze_decls(decls, known, *,
                  analyze_resolved=None,
                  handle_unresolved=True,
                  relroot=None,
                  ):
    knowntypes, knowntypespecs = _datafiles.get_known(
        known,
        handle_unresolved=handle_unresolved,
        analyze_resolved=analyze_resolved,
        relroot=relroot,
    )

    decls = list(decls)
    collated = group_by_kinds(decls)

    types = {decl: None for decl in collated['type']}
    typespecs = _analyze.get_typespecs(types)

    def analyze_decl(decl):
        return _analyze.analyze_decl(
            decl,
            typespecs,
            knowntypespecs,
            types,
            knowntypes,
            analyze_resolved=analyze_resolved,
        )
    _analyze.analyze_type_decls(types, analyze_decl, handle_unresolved)
    for decl in decls:
        if decl in types:
            resolved = types[decl]
        else:
            resolved = analyze_decl(decl)
            if resolved and handle_unresolved:
                typedeps, _ = resolved
                if not isinstance(typedeps, TypeDeclaration):
                    if not typedeps or None in typedeps:
                        raise NotImplementedError((decl, resolved))

        yield decl, resolved