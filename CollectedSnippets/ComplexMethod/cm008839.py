def orderedSet_from_options(options, alias_dict, *, use_regex=False, start=None):
    assert 'all' in alias_dict, '"all" alias is required'
    requested = list(start or [])
    for val in options:
        discard = val.startswith('-')
        if discard:
            val = val[1:]

        if val in alias_dict:
            val = alias_dict[val] if not discard else [
                i[1:] if i.startswith('-') else f'-{i}' for i in alias_dict[val]]
            # NB: Do not allow regex in aliases for performance
            requested = orderedSet_from_options(val, alias_dict, start=requested)
            continue

        current = (filter(re.compile(val, re.I).fullmatch, alias_dict['all']) if use_regex
                   else [val] if val in alias_dict['all'] else None)
        if current is None:
            raise ValueError(val)

        if discard:
            for item in current:
                while item in requested:
                    requested.remove(item)
        else:
            requested.extend(current)

    return orderedSet(requested)