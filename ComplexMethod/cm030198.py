def _check_types(a, b, *args):
    # Checking types is weird, but the alternative is garbled output when
    # someone passes mixed bytes and str to {unified,context}_diff(). E.g.
    # without this check, passing filenames as bytes results in output like
    #   --- b'oldfile.txt'
    #   +++ b'newfile.txt'
    # because of how str.format() incorporates bytes objects.
    if a and not isinstance(a[0], str):
        raise TypeError('lines to compare must be str, not %s (%r)' %
                        (type(a[0]).__name__, a[0]))
    if b and not isinstance(b[0], str):
        raise TypeError('lines to compare must be str, not %s (%r)' %
                        (type(b[0]).__name__, b[0]))
    if isinstance(a, str):
        raise TypeError('input must be a sequence of strings, not %s' %
                        type(a).__name__)
    if isinstance(b, str):
        raise TypeError('input must be a sequence of strings, not %s' %
                        type(b).__name__)
    for arg in args:
        if not isinstance(arg, str):
            raise TypeError('all arguments must be str, not: %r' % (arg,))