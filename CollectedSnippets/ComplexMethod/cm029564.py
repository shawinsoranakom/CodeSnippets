def in_build(f, dest="", new_name=None, no_lib=False):
        n, _, x = f.rpartition(".")
        n = new_name or n
        src = ns.build / f
        if ns.debug and src not in REQUIRED_DLLS:
            if not "_d." in src.name:
                src = src.parent / (src.stem + "_d" + src.suffix)
            if "_d." not in f:
                n += "_d"
                f = n + "." + x
        yield dest + n + "." + x, src
        if ns.include_symbols:
            pdb = src.with_suffix(".pdb")
            if pdb.is_file():
                yield dest + n + ".pdb", pdb
        if ns.include_dev and not no_lib:
            lib = src.with_suffix(".lib")
            if lib.is_file():
                yield "libs/" + n + ".lib", lib