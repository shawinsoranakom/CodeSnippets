def testformat(formatstr, args, output=None, limit=None, overflowok=False):
    if verbose:
        if output:
            print("{!a} % {!a} =? {!a} ...".format(formatstr, args, output),
                  end=' ')
        else:
            print("{!a} % {!a} works? ...".format(formatstr, args), end=' ')
    try:
        result = formatstr % args
    except OverflowError:
        if not overflowok:
            raise
        if verbose:
            print('overflow (this is fine)')
    else:
        if output and limit is None and result != output:
            if verbose:
                print('no')
            raise AssertionError("%r %% %r == %r != %r" %
                                (formatstr, args, result, output))
        # when 'limit' is specified, it determines how many characters
        # must match exactly; lengths must always match.
        # ex: limit=5, '12345678' matches '12345___'
        # (mainly for floating-point format tests for which an exact match
        # can't be guaranteed due to rounding and representation errors)
        elif output and limit is not None and (
                len(result)!=len(output) or result[:limit]!=output[:limit]):
            if verbose:
                print('no')
            print("%s %% %s == %s != %s" % \
                  (repr(formatstr), repr(args), repr(result), repr(output)))
        else:
            if verbose:
                print('yes')