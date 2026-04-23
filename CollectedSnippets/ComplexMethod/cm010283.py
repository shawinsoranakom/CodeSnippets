def _construct_inputs(
    gm: torch.fx.GraphModule,
    signature: ModuleCallSignature,
    node_name_map: dict[str, torch.fx.Node],
) -> tuple[list[torch.fx.Node], dict[str, torch.fx.Node]]:
    tree_unflatten_args: list[torch.fx.Node | None] = []
    for input_ in signature.inputs:
        if isinstance(input_, ConstantArgument) and input_.value is None:
            # Constants should be directly embedded into the graph and not used
            # as inputs
            tree_unflatten_args.append(None)
        elif input_.name not in node_name_map:
            # For unused inputs
            tree_unflatten_args.append(None)
        else:
            tree_unflatten_args.append(node_name_map[input_.name])

    # Insert unflatten call
    from .unflatten import _generate_unflatten

    unflatten_node = _generate_unflatten(gm, tree_unflatten_args, signature.in_spec)

    if signature.in_spec.num_children != 2:
        raise AssertionError(
            f"Expected in_spec to have 2 children, but got {signature.in_spec.num_children}"
        )
    if signature.in_spec.type is not tuple:
        raise AssertionError(
            f"Expected in_spec type to be tuple, but got {signature.in_spec.type}"
        )
    args_spec, kwargs_spec = signature.in_spec.children()
    if args_spec.type is not tuple:
        raise AssertionError(
            f"Expected args_spec type to be tuple, but got {args_spec.type}"
        )
    if kwargs_spec.type is not dict:
        raise AssertionError(
            f"Expected kwargs_spec type to be dict, but got {kwargs_spec.type}"
        )

    args_node = gm.graph.call_function(operator.getitem, (unflatten_node, 0))
    args_nodes = [
        gm.graph.call_function(operator.getitem, (args_node, i))
        for i in range(args_spec.num_children)
    ]
    kwargs_node = gm.graph.call_function(operator.getitem, (unflatten_node, 1))
    kwargs_nodes = {
        k: gm.graph.call_function(operator.getitem, (kwargs_node, k))
        for k in kwargs_spec.context
    }
    return args_nodes, kwargs_nodes