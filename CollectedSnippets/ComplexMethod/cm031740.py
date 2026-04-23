def makefreeze(base, dict, debug=0, entry_point=None, fail_import=()):
    if entry_point is None: entry_point = default_entry_point
    done = []
    files = []
    mods = sorted(dict.keys())
    for mod in mods:
        m = dict[mod]
        mangled = "__".join(mod.split("."))
        if m.__code__:
            file = 'M_' + mangled + '.c'
            with bkfile.open(base + file, 'w') as outfp:
                files.append(file)
                if debug:
                    print("freezing", mod, "...")
                str = marshal.dumps(m.__code__)
                size = len(str)
                is_package = '0'
                if m.__path__:
                    is_package = '1'
                done.append((mod, mangled, size, is_package))
                writecode(outfp, mangled, str)
    if debug:
        print("generating table of frozen modules")
    with bkfile.open(base + 'frozen.c', 'w') as outfp:
        for mod, mangled, size, _ in done:
            outfp.write('extern unsigned char M_%s[];\n' % mangled)
        outfp.write(header)
        for mod, mangled, size, is_package in done:
            outfp.write('\t{"%s", M_%s, %d, %s},\n' % (mod, mangled, size, is_package))
        outfp.write('\n')
        # The following modules have a NULL code pointer, indicating
        # that the frozen program should not search for them on the host
        # system. Importing them will *always* raise an ImportError.
        # The zero value size is never used.
        for mod in fail_import:
            outfp.write('\t{"%s", NULL, 0},\n' % (mod,))
        outfp.write(trailer)
        outfp.write(entry_point)
    return files