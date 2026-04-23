def get_layout(ns):
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

    source = "python.exe"
    sourcew = "pythonw.exe"
    alias = [
        "python",
        "python{}".format(VER_MAJOR) if ns.include_alias3 else "",
        "python{}".format(VER_DOT) if ns.include_alias3x else "",
    ]
    aliasw = [
        "pythonw",
        "pythonw{}".format(VER_MAJOR) if ns.include_alias3 else "",
        "pythonw{}".format(VER_DOT) if ns.include_alias3x else "",
    ]
    if ns.include_appxmanifest:
        source = "python_uwp.exe"
        sourcew = "pythonw_uwp.exe"
    elif ns.include_freethreaded:
        source = "python{}t.exe".format(VER_DOT)
        sourcew = "pythonw{}t.exe".format(VER_DOT)
        if not ns.include_alias:
            alias = []
            aliasw = []
        alias.extend([
            "python{}t".format(VER_DOT),
            "python{}t".format(VER_MAJOR) if ns.include_alias3 else None,
        ])
        aliasw.extend([
            "pythonw{}t".format(VER_DOT),
            "pythonw{}t".format(VER_MAJOR) if ns.include_alias3 else None,
        ])

    for a in filter(None, alias):
        yield from in_build(source, new_name=a)
    for a in filter(None, aliasw):
        yield from in_build(sourcew, new_name=a)

    if ns.include_freethreaded:
        yield from in_build(FREETHREADED_PYTHON_DLL_NAME)
    else:
        yield from in_build(PYTHON_DLL_NAME)

    if ns.include_launchers and ns.include_appxmanifest:
        if ns.include_pip:
            yield from in_build("python_uwp.exe", new_name="pip{}".format(VER_DOT))
        if ns.include_idle:
            yield from in_build("pythonw_uwp.exe", new_name="idle{}".format(VER_DOT))

    if ns.include_stable:
        if ns.include_freethreaded:
            yield from in_build(FREETHREADED_PYTHON_STABLE_DLL_NAME)
        else:
            yield from in_build(PYTHON_STABLE_DLL_NAME)

    found_any = False
    for dest, src in rglob(ns.build, "vcruntime*.dll"):
        found_any = True
        yield dest, src
    if not found_any:
        log_error("Failed to locate vcruntime DLL in the build.")

    yield "LICENSE.txt", ns.build / "LICENSE.txt"

    dest = "" if ns.flat_dlls else "DLLs/"

    for _, src in rglob(ns.build, "*.pyd"):
        if ns.include_freethreaded:
            if not src.match("*.cp*t-win*.pyd"):
                continue
            if bool(src.match("*_d.cp*.pyd")) != bool(ns.debug):
                continue
        else:
            if src.match("*.cp*t-win*.pyd"):
                continue
            if bool(src.match("*_d.pyd")) != bool(ns.debug):
                continue
        if src in TEST_PYDS_ONLY and not ns.include_tests:
            continue
        if src in TCLTK_PYDS_ONLY and not ns.include_tcltk:
            continue
        yield from in_build(src.name, dest=dest, no_lib=True)

    for _, src in rglob(ns.build, "*.dll"):
        if src.stem.endswith("_d") != bool(ns.debug) and src not in REQUIRED_DLLS:
            continue
        if src in EXCLUDE_FROM_DLLS:
            continue
        if src in TEST_DLLS_ONLY and not ns.include_tests:
            continue
        if src in TCLTK_DLLS_ONLY and not ns.include_tcltk:
            continue
        yield from in_build(src.name, dest=dest, no_lib=True)

    if ns.zip_lib:
        zip_name = PYTHON_ZIP_NAME
        yield zip_name, ns.temp / zip_name
    else:
        for dest, src in get_lib_layout(ns):
            yield "Lib/{}".format(dest), src

        if ns.include_venv:
            if ns.include_freethreaded:
                yield from in_build("venvlaunchert.exe", "Lib/venv/scripts/nt/")
                yield from in_build("venvwlaunchert.exe", "Lib/venv/scripts/nt/")
            elif (VER_MAJOR, VER_MINOR) > (3, 12):
                yield from in_build("venvlauncher.exe", "Lib/venv/scripts/nt/")
                yield from in_build("venvwlauncher.exe", "Lib/venv/scripts/nt/")
            else:
                # Older versions of venv expected the scripts to be named 'python'
                # and they were renamed at this stage. We need to replicate that
                # when packaging older versions.
                yield from in_build("venvlauncher.exe", "Lib/venv/scripts/nt/", "python")
                yield from in_build("venvwlauncher.exe", "Lib/venv/scripts/nt/", "pythonw")

    if ns.include_tools:

        def _c(d):
            if d.is_dir():
                return d in TOOLS_DIRS
            return d in TOOLS_FILES

        for dest, src in rglob(ns.source / "Tools", "**/*", _c):
            yield "Tools/{}".format(dest), src

    if ns.include_underpth:
        yield PYTHON_PTH_NAME, ns.temp / PYTHON_PTH_NAME

    if ns.include_dev:
        for dest, src in rglob(ns.source / "Include", "**/*.h"):
            yield "include/{}".format(dest), src
        # Support for layout of new and old releases.
        pc = ns.source / "PC"
        if (pc / "pyconfig.h.in").is_file():
            yield "include/pyconfig.h", ns.build / "pyconfig.h"
        else:
            yield "include/pyconfig.h", pc / "pyconfig.h"

    for dest, src in get_tcltk_lib(ns):
        yield dest, src

    if ns.include_pip:
        for dest, src in get_pip_layout(ns):
            if not isinstance(src, tuple) and (
                src in EXCLUDE_FROM_LIB or src in EXCLUDE_FROM_PACKAGED_LIB
            ):
                continue
            yield dest, src

    if ns.include_chm:
        for dest, src in rglob(ns.doc_build / "htmlhelp", PYTHON_CHM_NAME):
            yield "Doc/{}".format(dest), src

    if ns.include_html_doc:
        for dest, src in rglob(ns.doc_build / "html", "**/*"):
            yield "Doc/html/{}".format(dest), src

    if ns.include_props:
        for dest, src in get_props_layout(ns):
            yield dest, src

    if ns.include_nuspec:
        for dest, src in get_nuspec_layout(ns):
            yield dest, src

    for dest, src in get_appx_layout(ns):
        yield dest, src

    if ns.include_cat:
        if ns.flat_dlls:
            yield ns.include_cat.name, ns.include_cat
        else:
            yield "DLLs/{}".format(ns.include_cat.name), ns.include_cat

    if ns.include_install_json or ns.include_install_embed_json or ns.include_install_test_json:
        yield "__install__.json", ns.temp / "__install__.json"