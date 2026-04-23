def get_tcltk_lib(ns):
    if not ns.include_tcltk:
        return

    tcl_lib = os.getenv("TCL_LIBRARY")
    if not tcl_lib or not os.path.isdir(tcl_lib):
        try:
            with open(ns.build / "TCL_LIBRARY.env", "r", encoding="utf-8-sig") as f:
                tcl_lib = f.read().strip()
        except FileNotFoundError:
            pass
        if not tcl_lib or not os.path.isdir(tcl_lib):
            log_warning("Failed to find TCL_LIBRARY")
            return

    for dest, src in rglob(Path(tcl_lib).parent, "**/*"):
        yield "tcl/{}".format(dest), src