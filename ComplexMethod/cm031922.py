def _check_members(decl, typedeps, types, knowntypes):
    if isinstance(typedeps, TypeDeclaration):
        raise NotImplementedError((decl, typedeps))

    #members = decl.members or ()  # A forward decl has no members.
    members = decl.members
    if not members:
        # A forward decl has no members, but that shouldn't surface here..
        raise NotImplementedError(decl)
    if len(members) != len(typedeps):
        raise NotImplementedError((decl, typedeps))

    unsupported = []
    for member, typedecl in zip(members, typedeps):
        checked = _check_typedep(member, typedecl, types, knowntypes)
        unsupported.append(checked)
    if any(None if v is FIXED_TYPE else v for v in unsupported):
        return unsupported
    elif FIXED_TYPE in unsupported:
        return FIXED_TYPE
    else:
        return None