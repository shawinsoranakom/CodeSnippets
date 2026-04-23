def callfuncs(t):
    """ t is the testset. At this stage the testset contains operand lists
        t.cop and t.pop for the C and Python versions of decimal.
        For Decimal methods, the first operands are of type C.Decimal and
        P.Decimal respectively. The remaining operands can have various types.
        For Context methods, all operands can have any type.

        t.rc and t.rp are the results of the operation.
    """
    context.clear_status()
    t.maxcontext.clear_flags()

    try:
        if t.contextfunc:
            cargs = t.cop
            t.rc = getattr(context.c, t.funcname)(*cargs)
        else:
            cself = t.cop[0]
            cargs = t.cop[1:]
            t.rc = getattr(cself, t.funcname)(*cargs)
        t.cex.append(None)
    except (TypeError, ValueError, OverflowError, MemoryError) as e:
        t.rc = None
        t.cex.append(e.__class__)

    try:
        if t.contextfunc:
            pargs = t.pop
            t.rp = getattr(context.p, t.funcname)(*pargs)
        else:
            pself = t.pop[0]
            pargs = t.pop[1:]
            t.rp = getattr(pself, t.funcname)(*pargs)
        t.pex.append(None)
    except (TypeError, ValueError, OverflowError, MemoryError) as e:
        t.rp = None
        t.pex.append(e.__class__)

    # If the above results are exact, unrounded, normal etc., repeat the
    # operation with a maxcontext to ensure that huge intermediate values
    # do not cause a MemoryError.
    if (t.funcname not in MaxContextSkip and
        not context.c.flags[C.InvalidOperation] and
        not context.c.flags[C.Inexact] and
        not context.c.flags[C.Rounded] and
        not context.c.flags[C.Subnormal] and
        not context.c.flags[C.Clamped] and
        not context.clamp and # results are padded to context.prec if context.clamp==1.
        not any(isinstance(v, C.Context) for v in t.cop)): # another context is used.
        t.with_maxcontext = True
        try:
            if t.contextfunc:
                maxargs = t.maxop
                t.rmax = getattr(t.maxcontext, t.funcname)(*maxargs)
            else:
                maxself = t.maxop[0]
                maxargs = t.maxop[1:]
                try:
                    C.setcontext(t.maxcontext)
                    t.rmax = getattr(maxself, t.funcname)(*maxargs)
                finally:
                    C.setcontext(context.c)
            t.maxex.append(None)
        except (TypeError, ValueError, OverflowError, MemoryError) as e:
            t.rmax = None
            t.maxex.append(e.__class__)