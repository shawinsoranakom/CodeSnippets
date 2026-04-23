def _bless_my_loader(module_globals):
    # Similar to _bless_my_loader() in importlib._bootstrap_external,
    # but always emits warnings instead of errors.
    loader = module_globals.get('__loader__')
    if loader is None and '__spec__' not in module_globals:
        return None
    spec = module_globals.get('__spec__')

    # The __main__ module has __spec__ = None.
    if spec is None and module_globals.get('__name__') == '__main__':
        return loader

    spec_loader = getattr(spec, 'loader', None)
    if spec_loader is None:
        import warnings
        warnings.warn(
            'Module globals is missing a __spec__.loader',
            DeprecationWarning)
        return loader

    assert spec_loader is not None
    if loader is not None and loader != spec_loader:
        import warnings
        warnings.warn(
            'Module globals; __loader__ != __spec__.loader',
            DeprecationWarning)
        return loader

    return spec_loader