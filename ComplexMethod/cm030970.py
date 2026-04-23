def iter_slot_wrappers(cls):
    def is_slot_wrapper(name, value):
        if not isinstance(value, types.WrapperDescriptorType):
            assert not repr(value).startswith('<slot wrapper '), (cls, name, value)
            return False
        assert repr(value).startswith('<slot wrapper '), (cls, name, value)
        assert callable(value), (cls, name, value)
        assert name.startswith('__') and name.endswith('__'), (cls, name, value)
        return True

    try:
        attrs = identify_type_slot_wrappers()
    except NotImplementedError:
        attrs = None
    if attrs is not None:
        for attr in sorted(attrs):
            obj, base = find_name_in_mro(cls, attr, None)
            if obj is not None and is_slot_wrapper(attr, obj):
                yield attr, base is cls
        return

    # Fall back to a naive best-effort approach.

    ns = vars(cls)
    unused = set(ns)
    for name in dir(cls):
        if name in ns:
            unused.remove(name)

        try:
            value = getattr(cls, name)
        except AttributeError:
            # It's as though it weren't in __dir__.
            assert name in ('__annotate__', '__annotations__', '__abstractmethods__'), (cls, name)
            if name in ns and is_slot_wrapper(name, ns[name]):
                unused.add(name)
            continue

        if not name.startswith('__') or not name.endswith('__'):
            assert not is_slot_wrapper(name, value), (cls, name, value)
        if not is_slot_wrapper(name, value):
            if name in ns:
                assert not is_slot_wrapper(name, ns[name]), (cls, name, value, ns[name])
        else:
            if name in ns:
                assert ns[name] is value, (cls, name, value, ns[name])
                yield name, True
            else:
                yield name, False

    for name in unused:
        value = ns[name]
        if is_slot_wrapper(cls, name, value):
            yield name, True