def rekey_on_member(data, key, duplicates='error'):
    """
    Rekey a dict of dicts on another member

    May also create a dict from a list of dicts.

    duplicates can be one of ``error`` or ``overwrite`` to specify whether to error out if the key
    value would be duplicated or to overwrite previous entries if that's the case.
    """
    if duplicates not in ('error', 'overwrite'):
        raise AnsibleError(f"duplicates parameter to rekey_on_member has unknown value {duplicates!r}")

    new_obj = {}

    if isinstance(data, Mapping):
        iterate_over = data.values()
    elif isinstance(data, Iterable) and not isinstance(data, (str, bytes)):
        iterate_over = data
    else:
        raise AnsibleError("Type is not a valid list, set, or dict")

    for item in iterate_over:
        if not isinstance(item, Mapping):
            raise AnsibleError("List item is not a valid dict")

        try:
            key_elem = item[key]
        except KeyError:
            raise AnsibleError(f"Key {key!r} was not found.", obj=item) from None

        # Note: if new_obj[key_elem] exists it will always be a non-empty dict (it will at
        # minimum contain {key: key_elem}
        if new_obj.get(key_elem, None):
            if duplicates == 'error':
                raise AnsibleError(f"Key {key_elem!r} is not unique, cannot convert to dict.")
            elif duplicates == 'overwrite':
                new_obj[key_elem] = item
        else:
            new_obj[key_elem] = item

    return new_obj