def requireSocket(*args):
    """Skip decorated test if a socket cannot be created with given arguments.

    When an argument is given as a string, will use the value of that
    attribute of the socket module, or skip the test if it doesn't
    exist.  Sets client_skip attribute as skipWithClientIf() does.
    """
    err = None
    missing = [obj for obj in args if
               isinstance(obj, str) and not hasattr(socket, obj)]
    if missing:
        err = "don't have " + ", ".join(name for name in missing)
    else:
        callargs = [getattr(socket, obj) if isinstance(obj, str) else obj
                    for obj in args]
        try:
            s = socket.socket(*callargs)
        except OSError as e:
            # XXX: check errno?
            err = str(e)
        else:
            s.close()
    return skipWithClientIf(
        err is not None,
        "can't create socket({0}): {1}".format(
            ", ".join(str(o) for o in args), err))