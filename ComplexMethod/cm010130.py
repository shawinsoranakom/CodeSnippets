def _check_input_constraints_for_graph(
    input_placeholders: list[torch.fx.Node], flat_args_with_path, range_constraints
) -> None:
    if len(flat_args_with_path) != len(input_placeholders):
        raise RuntimeError(
            "Unexpected number of inputs "
            f"(expected {len(input_placeholders)}, got {len(flat_args_with_path)})"
        )
    # NOTE: export already guarantees that the same symbol is used in metadata
    # for all InputDims related by equality constraints, so we can just unify
    # symbols with given input dimension values to check equality constraints.
    unification_map: dict[sympy.Symbol, Any] = {}
    for (key_path, arg), node in zip(flat_args_with_path, input_placeholders):
        node_val = node.meta.get("val")
        if isinstance(node_val, FakeTensor):
            if not isinstance(arg, torch.Tensor):
                raise RuntimeError(
                    f"Expected input at {get_keystr(key_path)} to be a tensor, but got {type(arg)}",
                )

            if len(node_val.shape) != len(arg.shape):
                raise RuntimeError(
                    f"Unexpected number of dimensions in input at {get_keystr(key_path)}.shape "
                    f"(expected {node_val.shape}, got {arg.shape})"
                )

            for j, (arg_dim, node_dim) in enumerate(zip(arg.shape, node_val.shape)):
                _check_symint(
                    node_dim, arg_dim, range_constraints, unification_map, key_path, j
                )

        elif isinstance(node_val, (int, float, str)):
            if type(arg) is not type(node_val):
                raise RuntimeError(
                    f"Expected input at {get_keystr(key_path)} to be equal to {node_val}, but got {arg}",
                )
            # NaN != NaN in Python, so use math.isnan for NaN-to-NaN comparison
            if isinstance(node_val, float) and math.isnan(node_val):
                if not isinstance(arg, float) or not math.isnan(arg):
                    raise RuntimeError(
                        f"Expected input at {get_keystr(key_path)} to be nan, but got {arg}",
                    )
            elif arg != node_val:
                raise RuntimeError(
                    f"Expected input at {get_keystr(key_path)} to be equal to {node_val}, but got {arg}",
                )
        elif isinstance(node_val, torch.SymInt):
            _check_symint(
                node_val,
                arg,
                range_constraints,
                unification_map,
                key_path,
                None,
            )