def get_type_checker(v):
    v_type = v.get('type')
    if v_type == 'list':
        elt_checker, elt_name = get_type_checker({'type': v.get('elements')})

        def list_checker(value):
            if isinstance(value, str):
                value = [unquote(x.strip()) for x in value.split(',')]
            if not isinstance(value, list):
                raise ValueError('Value must be a list')
            if elt_checker:
                for elt in value:
                    try:
                        elt_checker(elt)
                    except Exception as exc:
                        raise ValueError('Entry %r is not of type %s: %s' % (elt, elt_name, exc))

        return list_checker, ('list of %s' % elt_name) if elt_checker else 'list'

    if v_type in ('boolean', 'bool'):
        return partial(boolean, strict=False), v_type

    if v_type in ('integer', 'int'):
        return int, v_type

    if v_type == 'float':
        return float, v_type

    if v_type == 'none':
        def none_checker(value):
            if value not in ('None', None):
                raise ValueError('Value must be "None" or none')

        return none_checker, v_type

    if v_type in ('str', 'string', 'path', 'tmp', 'temppath', 'tmppath'):
        def str_checker(value):
            if not isinstance(value, str):
                raise ValueError('Value must be string')

        return str_checker, v_type

    if v_type in ('pathspec', 'pathlist'):
        def path_list_checker(value):
            if not isinstance(value, str) and not is_iterable(value):
                raise ValueError('Value must be string or list of strings')

        return path_list_checker, v_type

    if v_type in ('dict', 'dictionary'):
        def dict_checker(value):
            if not isinstance(value, dict):
                raise ValueError('Value must be dictionary')

        return dict_checker, v_type

    return None, 'unknown'