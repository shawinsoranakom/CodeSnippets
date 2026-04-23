def resolve_decl(decl, typespecs, knowntypespecs, types):
    if decl.kind is KIND.ENUM:
        typedeps = []
    else:
        if decl.kind is KIND.VARIABLE:
            vartypes = [decl.vartype]
        elif decl.kind is KIND.FUNCTION:
            vartypes = [decl.signature.returntype]
        elif decl.kind is KIND.TYPEDEF:
            vartypes = [decl.vartype]
        elif decl.kind is KIND.STRUCT or decl.kind is KIND.UNION:
            vartypes = [m.vartype for m in decl.members]
        else:
            # Skip this one!
            return None

        typedeps = []
        for vartype in vartypes:
            typespec = vartype.typespec
            if is_pots(typespec):
                typedecl = POTSType(typespec)
            elif is_system_type(typespec):
                typedecl = SystemType(typespec)
            elif is_funcptr(vartype):
                typedecl = FuncPtr(vartype)
            else:
                typedecl = find_typedecl(decl, typespec, typespecs)
                if typedecl is None:
                    typedecl = find_typedecl(decl, typespec, knowntypespecs)
                elif not isinstance(typedecl, TypeDeclaration):
                    raise NotImplementedError(repr(typedecl))
                if typedecl is None:
                    # We couldn't find it!
                    typedecl = UNKNOWN
                elif typedecl not in types:
                    # XXX How can this happen?
                    typedecl = UNKNOWN
                elif types[typedecl] is UNKNOWN:
                    typedecl = UNKNOWN
                elif types[typedecl] is IGNORED:
                    # We don't care if it didn't resolve.
                    pass
                elif types[typedecl] is None:
                    # The typedecl for the typespec hasn't been resolved yet.
                    typedecl = None
            typedeps.append(typedecl)
    return typedeps