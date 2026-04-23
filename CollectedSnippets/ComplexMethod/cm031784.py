def get_localsplus_counts(code: types.CodeType,
                          names: tuple[str, ...],
                          kinds: bytes) -> tuple[int, int, int]:
    nlocals = 0
    ncellvars = 0
    nfreevars = 0
    assert len(names) == len(kinds)
    for name, kind in zip(names, kinds):
        if kind & CO_FAST_LOCAL:
            nlocals += 1
            if kind & CO_FAST_CELL:
                ncellvars += 1
        elif kind & CO_FAST_CELL:
            ncellvars += 1
        elif kind & CO_FAST_FREE:
            nfreevars += 1
    assert nlocals == len(code.co_varnames) == code.co_nlocals, \
        (nlocals, len(code.co_varnames), code.co_nlocals)
    assert ncellvars == len(code.co_cellvars)
    assert nfreevars == len(code.co_freevars)
    return nlocals, ncellvars, nfreevars