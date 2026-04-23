def assert_valid_override(parent_signature, child_signature, is_private):
    pparams = parent_signature.parameters
    cparams = child_signature.parameters

    # parent and child have exact same signature
    if pparams == cparams:
        return

    # parent has *args/**kwargs: child can define new custom args/kwargs
    parent_has_varargs = any(pp.kind == VAR_POSITIONAL for pp in pparams.values())
    parent_has_varkwargs = any(pp.kind == VAR_KEYWORD for pp in pparams.values())

    # child has *args/**kwargs: all unknown args/kargs are delegated
    child_has_varargs = any(cp.kind == VAR_POSITIONAL for cp in cparams.values())
    child_has_varkwargs = any(cp.kind == VAR_KEYWORD for cp in cparams.values())

    # check positionals
    pos_kinds = (POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD)
    pposparams = [pp for pp in pparams.values() if pp.kind in pos_kinds]
    cposparams = [cp for cp in cparams.values() if cp.kind in pos_kinds]
    if len(cposparams) < len(pposparams):
        assert child_has_varargs, "missing positional parameters"
        pposparams = pposparams[:len(cposparams)]
    elif len(cposparams) > len(pposparams):
        assert parent_has_varargs, "too many positional parameters"
        cposparams = cposparams[:len(pposparams)]
    for pparam, cparam in zip(pposparams, cposparams, strict=True):
        assert check_parameter(pparam, cparam, is_private=is_private), f"wrong positional parameter {cparam.name!r}"

    # check keywords
    kw_kinds = (KEYWORD_ONLY,) if is_private else (POSITIONAL_OR_KEYWORD, KEYWORD_ONLY)
    pkwparams = {pp_name: pp for pp_name, pp in pparams.items() if pp.kind in kw_kinds}
    ckwparams = {cp_name: cp for cp_name, cp in cparams.items() if cp.kind in kw_kinds}
    for name, pparam in pkwparams.items():
        cparam = ckwparams.get(name)
        if cparam is None:
            assert child_has_varkwargs, f"missing keyword parameter {name!r}"
        else:
            assert check_parameter(pparam, cparam, is_private=is_private), f"wrong keyword parameter {name!r}"
    if not parent_has_varkwargs:
        for name in (ckwparams.keys() - pkwparams.keys()):
            assert ckwparams[name].default is not EMPTY, "too many keyword parameters"