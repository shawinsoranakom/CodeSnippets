def _find_and_load_unlocked(name, import_):
    path = None
    sys.audit(
        "import",
        name,
        path,
        getattr(sys, "path", None),
        getattr(sys, "meta_path", None),
        getattr(sys, "path_hooks", None)
    )
    parent = name.rpartition('.')[0]
    parent_spec = None
    if parent:
        if parent not in sys.modules:
            _call_with_frames_removed(import_, parent)
        # Crazy side-effects!
        module = sys.modules.get(name)
        if module is not None:
            return module
        parent_module = sys.modules[parent]
        try:
            path = parent_module.__path__
        except AttributeError:
            msg = f'{_ERR_MSG_PREFIX}{name!r}; {parent!r} is not a package'
            raise ModuleNotFoundError(msg, name=name) from None
        parent_spec = parent_module.__spec__
        if getattr(parent_spec, '_initializing', False):
            _call_with_frames_removed(import_, parent)
        # Crazy side-effects (again)!
        module = sys.modules.get(name)
        if module is not None:
            return module
        child = name.rpartition('.')[2]
    spec = _find_spec(name, path)
    if spec is None:
        raise ModuleNotFoundError(f'{_ERR_MSG_PREFIX}{name!r}', name=name)
    else:
        if parent_spec:
            # Temporarily add child we are currently importing to parent's
            # _uninitialized_submodules for circular import tracking.
            parent_spec._uninitialized_submodules.append(child)
        try:
            module = _load_unlocked(spec)
        finally:
            if parent_spec:
                parent_spec._uninitialized_submodules.pop()
    if parent:
        # Set the module as an attribute on its parent.
        parent_module = sys.modules[parent]
        try:
            setattr(parent_module, child, module)
        except AttributeError:
            msg = f"Cannot set an attribute on {parent!r} for child module {child!r}"
            _warnings.warn(msg, ImportWarning)
    # Set attributes to lazy submodules on the module.
    try:
        _imp._set_lazy_attributes(module, name)
    except Exception as e:
        msg = f"Cannot set lazy attributes on {name!r}: {e!r}"
        _warnings.warn(msg, ImportWarning)
    return module