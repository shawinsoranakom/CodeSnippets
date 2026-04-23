def _iter_file_finder_modules(importer, prefix=''):
    if importer.path is None or not os.path.isdir(importer.path):
        return

    yielded = {}
    import inspect
    try:
        filenames = os.listdir(importer.path)
    except OSError:
        # ignore unreadable directories like import does
        filenames = []
    filenames.sort()  # handle packages before same-named modules

    for fn in filenames:
        modname = inspect.getmodulename(fn)
        if modname=='__init__' or modname in yielded:
            continue

        path = os.path.join(importer.path, fn)
        ispkg = False

        if not modname and os.path.isdir(path) and '.' not in fn:
            modname = fn
            try:
                dircontents = os.listdir(path)
            except OSError:
                # ignore unreadable directories like import does
                dircontents = []
            for fn in dircontents:
                subname = inspect.getmodulename(fn)
                if subname=='__init__':
                    ispkg = True
                    break
            else:
                continue    # not a package

        if modname and '.' not in modname:
            yielded[modname] = 1
            yield prefix + modname, ispkg