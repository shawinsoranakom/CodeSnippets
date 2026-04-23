def make_sourced_prefixes(nn_module, args, kwargs) -> _KeyPathTrie:
    kp_args, kp_kwargs = tree_map_with_path(
        lambda kp, _: _KeyPath(kp),
        (tuple(None for _ in args), {k: None for k in kwargs}),  # noqa: C420
    )
    kp_combined_args = _combine_args(nn_module, kp_args, kp_kwargs)

    sourced_prefixes = _KeyPathTrie()
    for name, struct in kp_combined_args.items():
        src = LocalSource(name)

        if isinstance(struct, _KeyPath):
            sourced_prefixes.add(struct.kp, src)
        elif isinstance(struct, tuple):
            for i, prefix in enumerate(struct):
                if not isinstance(prefix, _KeyPath):
                    raise AssertionError(f"expected _KeyPath, got {type(prefix)}")
                sourced_prefixes.add(prefix.kp, GetItemSource(src, i))
        elif isinstance(struct, dict):
            for k, prefix in struct.items():
                if not isinstance(prefix, _KeyPath):
                    raise AssertionError(f"expected _KeyPath, got {type(prefix)}")
                sourced_prefixes.add(prefix.kp, GetItemSource(src, k))

    return sourced_prefixes