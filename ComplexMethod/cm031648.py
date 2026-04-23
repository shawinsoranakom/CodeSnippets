def check(file):
    if os.path.isdir(file) and not os.path.islink(file):
        if verbose:
            print("listing directory", file)
        names = os.listdir(file)
        for name in names:
            fullname = os.path.join(file, name)
            if ((recurse and os.path.isdir(fullname) and
                 not os.path.islink(fullname) and
                 not os.path.split(fullname)[1].startswith("."))
                or name.lower().endswith(".py")):
                check(fullname)
        return

    if verbose:
        print("checking", file, "...", end=' ')
    with open(file, 'rb') as f:
        try:
            encoding, _ = tokenize.detect_encoding(f.readline)
        except SyntaxError as se:
            errprint("%s: SyntaxError: %s" % (file, str(se)))
            return
    try:
        with open(file, encoding=encoding) as f:
            r = Reindenter(f)
    except IOError as msg:
        errprint("%s: I/O Error: %s" % (file, str(msg)))
        return

    newline = spec_newline if spec_newline else r.newlines
    if isinstance(newline, tuple):
        errprint("%s: mixed newlines detected; cannot continue without --newline" % file)
        return

    if r.run():
        if verbose:
            print("changed.")
            if dryrun:
                print("But this is a dry run, so leaving it alone.")
        if not dryrun:
            bak = file + ".bak"
            if makebackup:
                shutil.copyfile(file, bak)
                if verbose:
                    print("backed up", file, "to", bak)
            with open(file, "w", encoding=encoding, newline=newline) as f:
                r.write(f)
            if verbose:
                print("wrote new", file)
        return True
    else:
        if verbose:
            print("unchanged.")
        return False