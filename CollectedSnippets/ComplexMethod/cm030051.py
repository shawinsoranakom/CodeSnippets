def _readmodule(module, path, inpackage=None):
    """Do the hard work for readmodule[_ex].

    If inpackage is given, it must be the dotted name of the package in
    which we are searching for a submodule, and then PATH must be the
    package search path; otherwise, we are searching for a top-level
    module, and path is combined with sys.path.
    """
    # Compute the full module name (prepending inpackage if set).
    if inpackage is not None:
        fullmodule = "%s.%s" % (inpackage, module)
    else:
        fullmodule = module

    # Check in the cache.
    if fullmodule in _modules:
        return _modules[fullmodule]

    # Initialize the dict for this module's contents.
    tree = {}

    # Check if it is a built-in module; we don't do much for these.
    if module in sys.builtin_module_names and inpackage is None:
        _modules[module] = tree
        return tree

    # Check for a dotted module name.
    i = module.rfind('.')
    if i >= 0:
        package = module[:i]
        submodule = module[i+1:]
        parent = _readmodule(package, path, inpackage)
        if inpackage is not None:
            package = "%s.%s" % (inpackage, package)
        if not '__path__' in parent:
            raise ImportError('No package named {}'.format(package))
        return _readmodule(submodule, parent['__path__'], package)

    # Search the path for the module.
    if inpackage is not None:
        search_path = path
    else:
        search_path = path + sys.path
    spec = importlib.util._find_spec_from_path(fullmodule, search_path)
    if spec is None:
        raise ModuleNotFoundError(f"no module named {fullmodule!r}", name=fullmodule)
    _modules[fullmodule] = tree
    # Is module a package?
    if spec.submodule_search_locations is not None:
        tree['__path__'] = spec.submodule_search_locations
    try:
        source = spec.loader.get_source(fullmodule)
    except (AttributeError, ImportError):
        # If module is not Python source, we cannot do anything.
        return tree
    else:
        if source is None:
            return tree

    fname = spec.loader.get_filename(fullmodule)
    return _create_tree(fullmodule, path, fname, source, tree, inpackage)