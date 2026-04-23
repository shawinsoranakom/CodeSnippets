def _get_locale_dirs(resources, include_core=True):
    """
    Return a tuple (contrib name, absolute path) for all locale directories,
    optionally including the django core catalog.
    If resources list is not None, filter directories matching resources
    content.
    """
    contrib_dir = os.path.join(os.getcwd(), "django", "contrib")
    dirs = []

    # Collect all locale directories
    for contrib_name in os.listdir(contrib_dir):
        path = os.path.join(contrib_dir, contrib_name, "locale")
        if os.path.isdir(path):
            dirs.append((contrib_name, path))
            if contrib_name in HAVE_JS:
                dirs.append(("%s-js" % contrib_name, path))
    if include_core:
        dirs.insert(0, ("core", os.path.join(os.getcwd(), "django", "conf", "locale")))

    # Filter by resources, if any
    if resources is not None:
        res_names = [d[0] for d in dirs]
        dirs = [ld for ld in dirs if ld[0] in resources]
        if len(resources) > len(dirs):
            print(
                "You have specified some unknown resources. "
                "Available resource names are: %s" % (", ".join(res_names),)
            )
            exit(1)
    return dirs