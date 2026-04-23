def lib_platform_files(dirname, names):
    """A file filter that ignores platform-specific files in lib."""
    path = Path(dirname)
    if (
        path.parts[-3] == "lib"
        and path.parts[-2].startswith("python")
        and path.parts[-1] == "lib-dynload"
    ):
        return names
    elif path.parts[-2] == "lib" and path.parts[-1].startswith("python"):
        ignored_names = {
            name
            for name in names
            if (
                name.startswith("_sysconfigdata_")
                or name.startswith("_sysconfig_vars_")
                or name == "build-details.json"
            )
        }
    elif path.parts[-1] == "lib":
        ignored_names = {
            name
            for name in names
            if name.startswith("libpython") and name.endswith(".dylib")
        }
    else:
        ignored_names = set()

    return ignored_names