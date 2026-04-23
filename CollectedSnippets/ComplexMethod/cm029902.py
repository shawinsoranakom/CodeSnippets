def _make_lazycache_entry(filename, module_globals):
    if not filename or (filename.startswith('<') and filename.endswith('>')):
        return None

    if module_globals is not None and not isinstance(module_globals, dict):
        raise TypeError(f'module_globals must be a dict, not {type(module_globals).__qualname__}')
    if not module_globals or '__name__' not in module_globals:
        return None

    spec = module_globals.get('__spec__')
    name = getattr(spec, 'name', None) or module_globals['__name__']
    if name is None:
        return None

    loader = _bless_my_loader(module_globals)
    if loader is None:
        return None

    get_source = getattr(loader, 'get_source', None)
    if get_source is None:
        return None

    def get_lines(name=name, *args, **kwargs):
        return get_source(name, *args, **kwargs)
    return (get_lines,)