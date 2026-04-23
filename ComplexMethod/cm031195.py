def reload(module):
    """Reload the module and return it.

    The module must have been successfully imported before.

    """
    try:
        name = module.__spec__.name
    except AttributeError:
        try:
            name = module.__name__
        except AttributeError:
            raise TypeError("reload() argument must be a module") from None

    if sys.modules.get(name) is not module:
        raise ImportError(f"module {name} not in sys.modules", name=name)
    if name in _RELOADING:
        return _RELOADING[name]
    _RELOADING[name] = module
    try:
        parent_name = name.rpartition('.')[0]
        if parent_name:
            try:
                parent = sys.modules[parent_name]
            except KeyError:
                raise ImportError(f"parent {parent_name!r} not in sys.modules",
                                  name=parent_name) from None
            else:
                pkgpath = parent.__path__
        else:
            pkgpath = None
        target = module
        spec = module.__spec__ = _bootstrap._find_spec(name, pkgpath, target)
        if spec is None:
            raise ModuleNotFoundError(f"spec not found for the module {name!r}", name=name)
        _bootstrap._exec(spec, module)
        # The module may have replaced itself in sys.modules!
        return sys.modules[name]
    finally:
        try:
            del _RELOADING[name]
        except KeyError:
            pass