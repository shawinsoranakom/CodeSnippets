def get_extractors() -> dict[str, list[str]]:  # noqa[C901]
    """Obtain a dictionary of all available extraction plugins by plugin type

    Returns
    -------
    A list of all available plugins for each extraction plugin type
    """
    root = os.path.join(PROJECT_ROOT, "plugins", "extract")
    folders = sorted(os.path.join(root, f) for f in os.listdir(root)
                     if os.path.isdir(os.path.join(root, f))
                     and not f.startswith("_"))
    retval: dict[str, list[str]] = {}
    for fld in folders:
        files = sorted(os.path.join(fld, fname) for fname in os.listdir(fld)
                       if os.path.isfile(os.path.join(fld, fname))
                       and fname.endswith(".py")
                       and not fname.startswith("_")
                       and not fname.endswith("_defaults.py"))
        mods = []
        for fpath in files:
            try:
                with open(fpath, "r", encoding="utf-8") as pfile:
                    tree = ast.parse(pfile.read())
            except Exception:  # pylint:disable=broad-except
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                for base in node.bases:
                    if not isinstance(base, ast.Name):
                        continue
                    if base.id in ("ExtractPlugin", "FacePlugin"):
                        rel_path = os.path.splitext(fpath.replace(PROJECT_ROOT, "")[1:])[0]
                        mods.append(".".join(full_path_split(rel_path) + [node.name]))
        if mods:
            retval[os.path.basename(fld)] = list(sorted(mods))
    logger.debug("Extraction plugins: %s", retval)
    return retval