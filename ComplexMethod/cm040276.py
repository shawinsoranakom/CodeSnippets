def _recursive_flatten_with_path(path, structure, flattened):
    registration = REGISTERED_CLASSES.get(type(structure), None)
    if registration is not None:
        flat_meta_paths = registration.flatten(structure)
        flat = flat_meta_paths[0]
        paths = (
            flat_meta_paths[2]
            if len(flat_meta_paths) >= 3
            else itertools.count()
        )
        for key, value in zip(paths, flat):
            _recursive_flatten_with_path(path + (key,), value, flattened)
    elif not dmtree.is_nested(structure):
        flattened.append((path, structure))
    elif isinstance(structure, collections.abc.Mapping):
        for key in sorted(structure):
            _recursive_flatten_with_path(
                path + (key,), structure[key], flattened
            )
    else:
        for key, value in enumerate(structure):
            _recursive_flatten_with_path(path + (key,), value, flattened)