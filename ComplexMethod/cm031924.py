def _check_typespec(decl, typedecl, types, knowntypes):
    typespec = decl.vartype.typespec
    if typedecl is not None:
        found = types.get(typedecl)
        if found is None:
            found = knowntypes.get(typedecl)

        if found is not None:
            _, extra = found
            if extra is None:
                # XXX Under what circumstances does this happen?
                extra = {}
            unsupported = extra.get('unsupported')
            if unsupported is FIXED_TYPE:
                unsupported = None
            return 'typespec' if unsupported else None
    # Fall back to default known types.
    if is_pots(typespec):
        return None
    elif is_system_type(typespec):
        return None
    elif is_funcptr(decl.vartype):
        return None
    return 'typespec'