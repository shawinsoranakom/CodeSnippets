def _stringify(value):
    """Internal function."""
    if isinstance(value, (list, tuple)):
        if len(value) == 1:
            value = _stringify(value[0])
            if _magic_re.search(value):
                value = '{%s}' % value
        else:
            value = '{%s}' % _join(value)
    else:
        if isinstance(value, bytes):
            value = str(value, 'latin1')
        else:
            value = str(value)
        if not value:
            value = '{}'
        elif _magic_re.search(value):
            # add '\' before special characters and spaces
            value = _magic_re.sub(r'\\\1', value)
            value = value.replace('\n', r'\n')
            value = _space_re.sub(r'\\\1', value)
            if value[0] == '"':
                value = '\\' + value
        elif value[0] == '"' or _space_re.search(value):
            value = '{%s}' % value
    return value