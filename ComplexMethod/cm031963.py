def _resolve_width(width, fmt, label, default):
    if width:
        if not isinstance(width, int):
            raise NotImplementedError
        return width
    elif fmt:
        parsed = _parse_fmt(fmt)
        if parsed:
            width, _ = parsed
            if width:
                return width

    if not default:
        return WIDTH
    elif hasattr(default, 'get'):
        defaults = default
        default = defaults.get(None) or WIDTH
        return defaults.get(label) or default
    else:
        return default or WIDTH