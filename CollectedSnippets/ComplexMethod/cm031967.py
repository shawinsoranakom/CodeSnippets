def analyze_type_decls(types, analyze_decl, handle_unresolved=True):
    unresolved = set(types)
    while unresolved:
        updated = []
        for decl in unresolved:
            resolved = analyze_decl(decl)
            if resolved is None:
                # The decl should be skipped or ignored.
                types[decl] = IGNORED
                updated.append(decl)
                continue
            typedeps, _ = resolved
            if typedeps is None:
                raise NotImplementedError(decl)
            if UNKNOWN in typedeps:
                # At least one dependency is unknown, so this decl
                # is not resolvable.
                types[decl] = UNKNOWN
                updated.append(decl)
                continue
            if None in typedeps:
                # XXX
                # Handle direct recursive types first.
                nonrecursive = 1
                if decl.kind is KIND.STRUCT or decl.kind is KIND.UNION:
                    nonrecursive = 0
                    i = 0
                    for member, dep in zip(decl.members, typedeps):
                        if dep is None:
                            if member.vartype.typespec != decl.shortkey:
                                nonrecursive += 1
                            else:
                                typedeps[i] = decl
                        i += 1
                if nonrecursive:
                    # We don't have all dependencies resolved yet.
                    continue
            types[decl] = resolved
            updated.append(decl)
        if updated:
            for decl in updated:
                unresolved.remove(decl)
        else:
            # XXX
            # Handle indirect recursive types.
            ...
            # We couldn't resolve the rest.
            # Let the caller deal with it!
            break
    if unresolved and handle_unresolved:
        if handle_unresolved is True:
            handle_unresolved = _handle_unresolved
        handle_unresolved(unresolved, types, analyze_decl)