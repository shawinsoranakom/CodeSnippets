def traverse_bottom_up(s):
        registration = REGISTERED_CLASSES.get(type(s), None)
        if registration is not None:
            flat_meta_s = registration.flatten(s)
            ret = [traverse_bottom_up(x) for x in list(flat_meta_s[0])]
            ret = registration.unflatten(flat_meta_s[1], ret)
        elif not dmtree.is_nested(s):
            ret = s
        elif isinstance(s, collections.abc.Mapping):
            ret = [traverse_bottom_up(s[key]) for key in sorted(s)]
            ret = dmtree._sequence_like(s, ret)
        else:
            ret = [traverse_bottom_up(x) for x in s]
            ret = dmtree._sequence_like(s, ret)
        func_ret = func(ret)
        return ret if func_ret is None else remap_map_to_none(func_ret, None)