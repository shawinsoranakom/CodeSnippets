def strip_internal_keys[T: Sequence | MutableMapping](dirty: T, exceptions: set[str] | frozenset[str] = frozenset()) -> T:
    """Recursively remove items from mappings whose keys start with `_ansible`, unless the key is in `exceptions`."""
    match dirty:
        case str():
            return dirty
        case Sequence():
            for element in dirty:
                strip_internal_keys(element, exceptions=exceptions)
        case MutableMapping():
            for key in list(dirty.keys()):
                if isinstance(key, str) and key.startswith('_ansible_') and key not in exceptions:
                    del dirty[key]
                else:
                    strip_internal_keys(dirty[key], exceptions=exceptions)

    return dirty