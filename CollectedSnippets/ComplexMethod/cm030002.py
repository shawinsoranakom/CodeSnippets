def _find_module(name, path=None):
    """An importlib reimplementation of imp.find_module (for our purposes)."""

    # It's necessary to clear the caches for our Finder first, in case any
    # modules are being added/deleted/modified at runtime. In particular,
    # test_modulefinder.py changes file tree contents in a cache-breaking way:

    importlib.machinery.PathFinder.invalidate_caches()

    spec = importlib.machinery.PathFinder.find_spec(name, path)

    if spec is None:
        raise ImportError("No module named {name!r}".format(name=name), name=name)

    # Some special cases:

    if spec.loader is importlib.machinery.BuiltinImporter:
        return None, None, ("", "", _C_BUILTIN)

    if spec.loader is importlib.machinery.FrozenImporter:
        return None, None, ("", "", _PY_FROZEN)

    file_path = spec.origin

    # On namespace packages, spec.loader might be None, but
    # spec.submodule_search_locations should always be set — check it instead.
    if isinstance(spec.submodule_search_locations, importlib.machinery.NamespacePath):
        return None, spec.submodule_search_locations, ("", "", _PKG_DIRECTORY)

    if spec.loader.is_package(name):  # non-namespace package
        return None, os.path.dirname(file_path), ("", "", _PKG_DIRECTORY)

    if isinstance(spec.loader, importlib.machinery.SourceFileLoader):
        kind = _PY_SOURCE

    elif isinstance(
        spec.loader, (
            importlib.machinery.ExtensionFileLoader,
            importlib.machinery.AppleFrameworkLoader,
        )
    ):
        kind = _C_EXTENSION

    elif isinstance(spec.loader, importlib.machinery.SourcelessFileLoader):
        kind = _PY_COMPILED

    else:  # Should never happen.
        return None, None, ("", "", _SEARCH_ERROR)

    file = io.open_code(file_path)
    suffix = os.path.splitext(file_path)[-1]

    return file, file_path, (suffix, "rb", kind)