def verify(t, stat):
    """ t is the testset. At this stage the testset contains the following
        tuples:

            t.op: original operands
            t.cop: C.Decimal operands (see convert for details)
            t.pop: P.Decimal operands (see convert for details)
            t.rc: C result
            t.rp: Python result

        t.rc and t.rp can have various types.
    """
    t.cresults.append(str(t.rc))
    t.presults.append(str(t.rp))
    if t.with_maxcontext:
        t.maxresults.append(str(t.rmax))

    if isinstance(t.rc, C.Decimal) and isinstance(t.rp, P.Decimal):
        # General case: both results are Decimals.
        t.cresults.append(t.rc.to_eng_string())
        t.cresults.append(t.rc.as_tuple())
        t.cresults.append(str(t.rc.imag))
        t.cresults.append(str(t.rc.real))
        t.presults.append(t.rp.to_eng_string())
        t.presults.append(t.rp.as_tuple())
        t.presults.append(str(t.rp.imag))
        t.presults.append(str(t.rp.real))

        if t.with_maxcontext and isinstance(t.rmax, C.Decimal):
            t.maxresults.append(t.rmax.to_eng_string())
            t.maxresults.append(t.rmax.as_tuple())
            t.maxresults.append(str(t.rmax.imag))
            t.maxresults.append(str(t.rmax.real))

        nc = t.rc.number_class().lstrip('+-s')
        stat[nc] += 1
    else:
        # Results from e.g. __divmod__ can only be compared as strings.
        if not isinstance(t.rc, tuple) and not isinstance(t.rp, tuple):
            if t.rc != t.rp:
                raise_error(t)
            if t.with_maxcontext and not isinstance(t.rmax, tuple):
                if t.rmax != t.rc:
                    raise_error(t)
        stat[type(t.rc).__name__] += 1

    # The return value lists must be equal.
    if t.cresults != t.presults:
        raise_error(t)
    # The Python exception lists (TypeError, etc.) must be equal.
    if t.cex != t.pex:
        raise_error(t)
    # The context flags must be equal.
    if not t.context.assert_eq_status():
        raise_error(t)

    if t.with_maxcontext:
        # NaN payloads etc. depend on precision and clamp.
        if all_nan(t.rc) and all_nan(t.rmax):
            return
        # The return value lists must be equal.
        if t.maxresults != t.cresults:
            raise_error(t)
        # The Python exception lists (TypeError, etc.) must be equal.
        if t.maxex != t.cex:
            raise_error(t)
        # The context flags must be equal.
        if t.maxcontext.flags != t.context.c.flags:
            raise_error(t)