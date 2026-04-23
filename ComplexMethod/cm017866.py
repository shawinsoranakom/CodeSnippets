def iter_modules_and_files(modules, extra_files):
    """Iterate through all modules needed to be watched."""
    sys_file_paths = []
    for module in modules:
        # During debugging (with PyDev) the 'typing.io' and 'typing.re' objects
        # are added to sys.modules, however they are types not modules and so
        # cause issues here.
        if not isinstance(module, ModuleType):
            continue
        if module.__name__ in ("__main__", "__mp_main__"):
            # __main__ (usually manage.py) doesn't always have a __spec__ set.
            # Handle this by falling back to using __file__, resolved below.
            # See https://docs.python.org/reference/import.html#main-spec
            # __file__ may not exists, e.g. when running ipdb debugger.
            if hasattr(module, "__file__"):
                sys_file_paths.append(module.__file__)
            continue
        if getattr(module, "__spec__", None) is None:
            continue
        spec = module.__spec__
        # Modules could be loaded from places without a concrete location. If
        # this is the case, skip them.
        if spec.has_location:
            origin = (
                spec.loader.archive
                if isinstance(spec.loader, zipimporter)
                else spec.origin
            )
            sys_file_paths.append(origin)

    results = set()
    for filename in itertools.chain(sys_file_paths, extra_files):
        if not filename:
            continue
        path = Path(filename)
        try:
            if not path.exists():
                # The module could have been removed, don't fail loudly if this
                # is the case.
                continue
        except ValueError as e:
            # Network filesystems may return null bytes in file paths.
            logger.debug('"%s" raised when resolving path: "%s"', e, path)
            continue
        resolved_path = path.resolve().absolute()
        results.add(resolved_path)
    return frozenset(results)