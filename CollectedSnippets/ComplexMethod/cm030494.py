def open(file, flag='r', mode=0o666):
    """Open or create database at path given by *file*.

    Optional argument *flag* can be 'r' (default) for read-only access, 'w'
    for read-write access of an existing database, 'c' for read-write access
    to a new or existing database, and 'n' for read-write access to a new
    database.

    Note: 'r' and 'w' fail if the database doesn't exist; 'c' creates it
    only if it doesn't exist; and 'n' always creates a new database.
    """
    global _defaultmod
    if _defaultmod is None:
        for name in _names:
            try:
                mod = __import__(name, fromlist=['open'])
            except ImportError:
                continue
            if not _defaultmod:
                _defaultmod = mod
            _modules[name] = mod
        if not _defaultmod:
            raise ImportError("no dbm clone found; tried %s" % _names)

    # guess the type of an existing database, if not creating a new one
    result = whichdb(file) if 'n' not in flag else None
    if result is None:
        # db doesn't exist or 'n' flag was specified to create a new db
        if 'c' in flag or 'n' in flag:
            # file doesn't exist and the new flag was used so use default type
            mod = _defaultmod
        else:
            raise error[0]("db file doesn't exist; "
                           "use 'c' or 'n' flag to create a new db")
    elif result == "":
        # db type cannot be determined
        raise error[0]("db type could not be determined")
    elif result not in _modules:
        raise error[0]("db type is {0}, but the module is not "
                       "available".format(result))
    else:
        mod = _modules[result]
    return mod.open(file, flag, mode)