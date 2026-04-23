def _create_subgraph_for_node(
    graph: fx.Graph, node: fx.Node, additional_deps=None
) -> fx.GraphModule:
    """
    Create a subgraph that exactly recreates a node's operation optionally passing through additional dependencies.

    The subgraph takes only the fx.Node arguments and recreates the operation
    with the exact target, args structure, and kwargs.

    Args:
        graph: The parent graph
        node: The node to wrap in a subgraph
        additional_deps: Additional dependencies to pass through the subgraph

    Returns:
        A GraphModule containing the subgraph
    """
    # Get the owning module
    owning_module = graph.owning_module

    # Create a new graph for the subgraph
    subgraph = fx.Graph(owning_module)

    # Extract unique nodes and get flattened structure + spec
    unique_nodes, flat_args_kwargs, spec = _extract_unique_nodes(node.args, node.kwargs)

    # Create placeholders for each unique node
    node_to_placeholder: dict[fx.Node, fx.Node] = {}
    for idx, orig_node in enumerate(unique_nodes):
        placeholder = subgraph.placeholder(f"arg_{idx}")
        if "val" in orig_node.meta:
            placeholder.meta.update(orig_node.meta)
        node_to_placeholder[orig_node] = placeholder

    # Replace fx.Node instances with their placeholders
    def replace_nodes(item: Any) -> Any:
        if isinstance(item, fx.Node):
            return node_to_placeholder[item]
        return item

    additional_deps_placeholders = []
    for idx, dep in enumerate(additional_deps or ()):
        placeholder = subgraph.placeholder(f"dep_{idx}")
        if "val" in dep.meta:
            placeholder.meta.update(dep.meta)
        additional_deps_placeholders.append(placeholder)

    new_flat = [replace_nodes(item) for item in flat_args_kwargs]
    new_args, new_kwargs = pytree.tree_unflatten(new_flat, spec)

    # Recreate the exact original operation in the subgraph
    assert callable(node.target)
    result = subgraph.call_function(
        node.target,
        tuple(new_args),
        new_kwargs,  # type: ignore[arg-type]
    )

    # Copy metadata from the original node
    result.meta.update(node.meta)

    if additional_deps_placeholders:
        outputs = tuple([result] + additional_deps_placeholders)
        out = subgraph.output(outputs)
        out.meta["val"] = tuple(output.meta.get("val") for output in outputs)
    else:
        out = subgraph.output(result)
        if "val" in result.meta:
            out.meta["val"] = result.meta["val"]

    return fx.GraphModule(owning_module, subgraph)