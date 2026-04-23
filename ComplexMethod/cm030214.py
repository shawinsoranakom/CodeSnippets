def _find_incompatible_extension_module(module_name):
    import importlib.machinery
    import importlib.resources.readers

    if not module_name or not importlib.machinery.EXTENSION_SUFFIXES:
        return

    # We assume the last extension is untagged (eg. .so, .pyd)!
    # tests.test_traceback.MiscTest.test_find_incompatible_extension_modules
    # tests that assumption.
    untagged_suffix = importlib.machinery.EXTENSION_SUFFIXES[-1]
    # On Windows the debug tag is part of the module file stem, instead of the
    # extension (eg. foo_d.pyd), so let's remove it and just look for .pyd.
    if os.name == 'nt':
        untagged_suffix = untagged_suffix.removeprefix('_d')

    parent, _, child = module_name.rpartition('.')
    if parent:
        traversable = importlib.resources.files(parent)
    else:
        traversable = importlib.resources.readers.MultiplexedPath(
            *map(pathlib.Path, filter(os.path.isdir, sys.path))
        )

    for entry in traversable.iterdir():
        if entry.name.startswith(child + '.') and entry.name.endswith(untagged_suffix):
            return entry.name