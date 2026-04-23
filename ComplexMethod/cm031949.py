def iter_files(root, suffix=None, relparent=None, *,
               get_files=os.walk,
               _glob=glob_tree,
               _walk=walk_tree,
               ):
    """Yield each file in the tree under the given directory name.

    If "root" is a non-string iterable then do the same for each of
    those trees.

    If "suffix" is provided then only files with that suffix will
    be included.

    if "relparent" is provided then it is used to resolve each
    filename as a relative path.
    """
    if not isinstance(root, str):
        roots = root
        for root in roots:
            yield from iter_files(root, suffix, relparent,
                                  get_files=get_files,
                                  _glob=_glob, _walk=_walk)
        return

    # Use the right "walk" function.
    if get_files in (glob.glob, glob.iglob, glob_tree):
        get_files = _glob
    else:
        _files = _walk_tree if get_files in (os.walk, walk_tree) else get_files
        get_files = (lambda *a, **k: _walk(*a, walk=_files, **k))

    # Handle a single suffix.
    if suffix and not isinstance(suffix, str):
        filenames = get_files(root)
        suffix = tuple(suffix)
    else:
        filenames = get_files(root, suffix=suffix)
        suffix = None

    for filename in filenames:
        if suffix and not isinstance(suffix, str):  # multiple suffixes
            if not filename.endswith(suffix):
                continue
        if relparent:
            filename = os.path.relpath(filename, relparent)
        yield filename