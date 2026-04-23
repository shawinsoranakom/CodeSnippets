def parse_native_yaml_struct(
    es: object,
    valid_tags: set[str],
    ignore_keys: set[DispatchKey] | None = None,
    path: str = "<stdin>",
    skip_native_fns_gen: bool = False,
) -> ParsedYaml:
    if not isinstance(es, list):
        raise AssertionError(f"Expected 'es' to be a list, but got {type(es)}")
    rs: list[NativeFunction] = []
    bs: dict[DispatchKey, dict[OperatorName, BackendMetadata]] = defaultdict(dict)
    for e in es:
        if not isinstance(e, dict):
            raise AssertionError(f"Expected to be dict: {e}")
        if not isinstance(e.get("__line__"), int):
            raise AssertionError(f"Expected '__line__' to be int: {e}")
        loc = Location(path, e["__line__"])
        funcs = e.get("func")
        if funcs is None:
            raise AssertionError(f"Missed 'func' in {e}")
        with context(lambda: f"in {loc}:\n  {funcs}"):
            func, m = NativeFunction.from_yaml(e, loc, valid_tags, ignore_keys)
            rs.append(func)
            BackendIndex.grow_index(bs, m)
    error_check_native_functions(rs)
    # Default dict is to prevent the codegen from barfing when we have a dispatch key that has no kernels yet.
    indices: dict[DispatchKey, BackendIndex] = defaultdict(
        lambda: BackendIndex(
            dispatch_key=DispatchKey.Undefined,
            use_out_as_primary=True,
            external=False,
            device_guard=False,
            # I'm actually not sure about this; undefined could be hit on
            # empty TensorList, hypothetically that could have sizes in it
            index={},
        )
    )
    if not skip_native_fns_gen:
        add_generated_native_functions(rs, bs)
    for k, v in bs.items():
        # All structured in-tree operators are implemented in terms of their out operator.
        indices[k] = BackendIndex(
            dispatch_key=k,
            use_out_as_primary=True,
            external=False,
            # Only cuda-like devices in tree require device guards
            device_guard=is_cuda_dispatch_key(k) or is_xpu_dispatch_key(k),
            index=v,
        )
    return ParsedYaml(rs, indices)