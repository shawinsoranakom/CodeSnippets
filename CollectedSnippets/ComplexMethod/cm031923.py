def _check_typedep(decl, typedecl, types, knowntypes):
    if not isinstance(typedecl, TypeDeclaration):
        if hasattr(type(typedecl), '__len__'):
            if len(typedecl) == 1:
                typedecl, = typedecl
    if typedecl is None:
        # XXX Fail?
        return 'typespec (missing)'
    elif typedecl is _info.UNKNOWN:
        if _has_other_supported_type(decl):
            return None
        # XXX Is this right?
        return 'typespec (unknown)'
    elif not isinstance(typedecl, TypeDeclaration):
        raise NotImplementedError((decl, typedecl))

    if isinstance(decl, Member):
        return _check_vartype(decl, typedecl, types, knowntypes)
    elif not isinstance(decl, Declaration):
        raise NotImplementedError(decl)
    elif decl.kind is KIND.TYPEDEF:
        return _check_vartype(decl, typedecl, types, knowntypes)
    elif decl.kind is KIND.VARIABLE:
        if not is_process_global(decl):
            return None
        if _is_kwlist(decl):
            return None
        if _has_other_supported_type(decl):
            return None
        checked = _check_vartype(decl, typedecl, types, knowntypes)
        return 'mutable' if checked is FIXED_TYPE else checked
    else:
        raise NotImplementedError(decl)