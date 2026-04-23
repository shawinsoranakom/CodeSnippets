def select(e, mods, vars, mod, skipofiles):
    files = []
    for w in mods[mod]:
        w = treatword(w)
        if not w:
            continue
        w = expandvars(w, vars)
        for w in w.split():
            if skipofiles and w[-2:] == '.o':
                continue
            # Assume $var expands to absolute pathname
            if w[0] not in ('-', '$') and w[-2:] in ('.o', '.a'):
                w = os.path.join(e, w)
            if w[:2] in ('-L', '-R') and w[2:3] != '$':
                w = w[:2] + os.path.join(e, w[2:])
            files.append(w)
    return files