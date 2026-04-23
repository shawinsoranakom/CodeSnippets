def find_typedecl(decl, typespec, typespecs):
    specdecls = typespecs.get(typespec)
    if not specdecls:
        return None

    filename = decl.filename

    if len(specdecls) == 1:
        typedecl, = specdecls
        if '-' in typespec and typedecl.filename != filename:
            # Inlined types are always in the same file.
            return None
        return typedecl

    # Decide which one to return.
    candidates = []
    samefile = None
    for typedecl in specdecls:
        type_filename = typedecl.filename
        if type_filename == filename:
            if samefile is not None:
                # We expect type names to be unique in a file.
                raise NotImplementedError((decl, samefile, typedecl))
            samefile = typedecl
        elif filename.endswith('.c') and not type_filename.endswith('.h'):
            # If the decl is in a source file then we expect the
            # type to be in the same file or in a header file.
            continue
        candidates.append(typedecl)
    if not candidates:
        return None
    elif len(candidates) == 1:
        winner, = candidates
        # XXX Check for inline?
    elif '-' in typespec:
        # Inlined types are always in the same file.
        winner = samefile
    elif samefile is not None:
        # Favor types in the same file.
        winner = samefile
    else:
        # We don't know which to return.
        raise NotImplementedError((decl, candidates))

    return winner