def merge_dicts(*dicts, **kwargs):
    """
        Merge the `dict`s in `dicts` using the first valid value for each key.
        Normally valid: not None and not an empty string

        Keyword-only args:
        unblank:    allow empty string if False (default True)
        rev:        merge dicts in reverse order (default False)

        merge_dicts(dct1, dct2, ..., unblank=False, rev=True)
        matches {**dct1, **dct2, ...}

        However, merge_dicts(dct1, dct2, ..., rev=True) may often be better.
    """

    unblank = kwargs.get('unblank', True)
    rev = kwargs.get('rev', False)

    if unblank:
        def can_merge_str(k, v, to_dict):
            return (isinstance(v, compat_str) and v
                    and isinstance(to_dict[k], compat_str)
                    and not to_dict[k])
    else:
        can_merge_str = lambda k, v, to_dict: False

    merged = {}
    for a_dict in reversed(dicts) if rev else dicts:
        for k, v in a_dict.items():
            if v is None:
                continue
            if (k not in merged) or can_merge_str(k, v, merged):
                merged[k] = v
    return merged