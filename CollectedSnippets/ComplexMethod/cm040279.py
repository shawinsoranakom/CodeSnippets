def flatten_with_path(structure):
    # We need to first sort dicts to ensure a deterministic order that is
    # consistent with other tree implementations.
    structure = _dict_to_ordered_dict(structure)
    leaves_with_path, _ = torch_tree.tree_flatten_with_path(structure)
    results = []
    fields = []
    for key, leaf in leaves_with_path:
        for k in key:
            if isinstance(k, torch_tree.GetAttrKey) and k.name not in fields:
                fields.append(k.name)
    fields = sorted(fields)
    field_to_idx = {f: i for i, f in enumerate(fields)}
    for key, leaf in leaves_with_path:
        # Convert to a tuple of keys.
        path = []
        for k in key:
            if isinstance(k, torch_tree.SequenceKey):
                path.append(k.idx)
            elif isinstance(k, torch_tree.MappingKey):
                path.append(k.key)
            elif isinstance(k, torch_tree.GetAttrKey):
                path.append(field_to_idx[k.name])
        results.append((tuple(path), leaf))
    return results