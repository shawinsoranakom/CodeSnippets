def container_to_bytes(d, encoding='utf-8', errors='surrogate_or_strict'):
    """ Recursively convert dict keys and values to byte str

        Specialized for json return because this only handles, lists, tuples,
        and dict container types (the containers that the json module returns)
    """
    # DTFIX-FUTURE: deprecate

    if isinstance(d, str):
        return to_bytes(d, encoding=encoding, errors=errors)
    elif isinstance(d, dict):
        return dict(container_to_bytes(o, encoding, errors) for o in d.items())
    elif isinstance(d, list):
        return [container_to_bytes(o, encoding, errors) for o in d]
    elif isinstance(d, tuple):
        return tuple(container_to_bytes(o, encoding, errors) for o in d)
    else:
        return d