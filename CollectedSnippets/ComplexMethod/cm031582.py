def convert(t, convstr=True):
    """ t is the testset. At this stage the testset contains a tuple of
        operands t.op of various types. For decimal methods the first
        operand (self) is always converted to Decimal. If 'convstr' is
        true, string operands are converted as well.

        Context operands are of type deccheck.Context, rounding mode
        operands are given as a tuple (C.rounding, P.rounding).

        Other types (float, int, etc.) are left unchanged.
    """
    for i, op in enumerate(t.op):

        context.clear_status()
        t.maxcontext.clear_flags()

        if op in RoundModes:
            t.cop.append(op)
            t.pop.append(op)
            t.maxop.append(op)

        elif not t.contextfunc and i == 0 or \
             convstr and isinstance(op, str):
            try:
                c = C.Decimal(op)
                cex = None
            except (TypeError, ValueError, OverflowError) as e:
                c = None
                cex = e.__class__

            try:
                p = RestrictedDecimal(op)
                pex = None
            except (TypeError, ValueError, OverflowError) as e:
                p = None
                pex = e.__class__

            try:
                C.setcontext(t.maxcontext)
                maxop = C.Decimal(op)
                maxex = None
            except (TypeError, ValueError, OverflowError) as e:
                maxop = None
                maxex = e.__class__
            finally:
                C.setcontext(context.c)

            t.cop.append(c)
            t.cex.append(cex)

            t.pop.append(p)
            t.pex.append(pex)

            t.maxop.append(maxop)
            t.maxex.append(maxex)

            if cex is pex:
                if str(c) != str(p) or not context.assert_eq_status():
                    raise_error(t)
                if cex and pex:
                    # nothing to test
                    return 0
            else:
                raise_error(t)

            # The exceptions in the maxcontext operation can legitimately
            # differ, only test that maxex implies cex:
            if maxex is not None and cex is not maxex:
                raise_error(t)

        elif isinstance(op, Context):
            t.context = op
            t.cop.append(op.c)
            t.pop.append(op.p)
            t.maxop.append(t.maxcontext)

        else:
            t.cop.append(op)
            t.pop.append(op)
            t.maxop.append(op)

    return 1