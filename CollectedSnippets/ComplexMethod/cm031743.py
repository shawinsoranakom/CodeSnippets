def checkextensions(unknown, extensions):
    files = []
    modules = []
    edict = {}
    for e in extensions:
        setup = os.path.join(e, 'Setup')
        liba = os.path.join(e, 'lib.a')
        if not os.path.isfile(liba):
            liba = None
        edict[e] = parsesetup.getsetupinfo(setup), liba
    for mod in unknown:
        for e in extensions:
            (mods, vars), liba = edict[e]
            if mod not in mods:
                continue
            modules.append(mod)
            if liba:
                # If we find a lib.a, use it, ignore the
                # .o files, and use *all* libraries for
                # *all* modules in the Setup file
                if liba in files:
                    break
                files.append(liba)
                for m in list(mods.keys()):
                    files = files + select(e, mods, vars,
                                           m, 1)
                break
            files = files + select(e, mods, vars, mod, 0)
            break
    return files, modules