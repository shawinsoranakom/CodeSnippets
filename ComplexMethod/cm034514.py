def wrap_var(v):
    # maintain backward compat by recursively *un* marking TrustedAsTemplate
    if v is None or isinstance(v, AnsibleUnsafe):
        return v

    if isinstance(v, Mapping):
        v = _wrap_dict(v)
    elif isinstance(v, Set):
        v = _wrap_set(v)
    elif is_sequence(v):
        v = _wrap_sequence(v)
    elif isinstance(v, bytes):
        v = AnsibleUnsafeBytes(v)
    elif isinstance(v, str):
        v = AnsibleUnsafeText(v)

    return v