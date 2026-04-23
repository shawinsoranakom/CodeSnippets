def iter_zipimport_modules(importer, prefix=''):
        dirlist = sorted(zipimport._zip_directory_cache[importer.archive])
        _prefix = importer.prefix
        plen = len(_prefix)
        yielded = {}
        import inspect
        for fn in dirlist:
            if not fn.startswith(_prefix):
                continue

            fn = fn[plen:].split(os.sep)

            if len(fn)==2 and fn[1].startswith('__init__.py'):
                if fn[0] not in yielded:
                    yielded[fn[0]] = 1
                    yield prefix + fn[0], True

            if len(fn)!=1:
                continue

            modname = inspect.getmodulename(fn[0])
            if modname=='__init__':
                continue

            if modname and '.' not in modname and modname not in yielded:
                yielded[modname] = 1
                yield prefix + modname, False