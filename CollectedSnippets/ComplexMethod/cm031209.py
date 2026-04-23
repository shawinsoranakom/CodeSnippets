def _bless_my_loader(module_globals):
    """Helper function for _warnings.c

    See GH#97850 for details.
    """
    # 2022-10-06(warsaw): For now, this helper is only used in _warnings.c and
    # that use case only has the module globals.  This function could be
    # extended to accept either that or a module object.  However, in the
    # latter case, it would be better to raise certain exceptions when looking
    # at a module, which should have either a __loader__ or __spec__.loader.
    # For backward compatibility, it is possible that we'll get an empty
    # dictionary for the module globals, and that cannot raise an exception.
    if not isinstance(module_globals, dict):
        return None

    missing = object()
    loader = module_globals.get('__loader__', None)
    spec = module_globals.get('__spec__', missing)

    if loader is None:
        if spec is missing:
            # If working with a module:
            # raise AttributeError('Module globals is missing a __spec__')
            return None
        elif spec is None:
            raise ValueError('Module globals is missing a __spec__.loader')

    spec_loader = getattr(spec, 'loader', missing)

    if spec_loader in (missing, None):
        if loader is None:
            exc = AttributeError if spec_loader is missing else ValueError
            raise exc('Module globals is missing a __spec__.loader')
        _warnings.warn(
            'Module globals is missing a __spec__.loader',
            DeprecationWarning)
        spec_loader = loader

    assert spec_loader is not None
    if loader is not None and loader != spec_loader:
        _warnings.warn(
            'Module globals; __loader__ != __spec__.loader',
            DeprecationWarning)
        return loader

    return spec_loader