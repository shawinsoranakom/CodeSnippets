def return_first_non_observer_node(
    node: Node,
    gm: GraphModule,
) -> Node:
    """
    If node is not an observer, returns it.  If node is an observer,
    navigates up the graph and returns the first parent which is not an
    observer.  For example,

    graph: (node_non_obs), node = node_non_obs : returns node_non_obs
    graph: (node_non_obs -> obs0), node = obs0 : returns node_non_obs
    graph: (node_non_obs -> obs0 -> fq0), node = fq0 : returns node_non_obs
    """
    if node.op == "call_module":
        node_obj = getattr_from_fqn(gm, node.target)  # type: ignore[arg-type]
        if _is_activation_post_process(node_obj):
            if len(node.args) != 1:
                raise AssertionError(
                    f"Expected node.args to have length 1, got {len(node.args)}"
                )
            if not isinstance(node.args[0], Node):
                raise AssertionError(f"Expected Node, got {type(node.args[0])}")
            node = node.args[0]
            # code duplication intended, not worth refactoring
            if not isinstance(node.target, str):
                raise AssertionError(f"Expected str, got {type(node.target)}")
            node_obj = getattr_from_fqn(gm, node.target)
            if _is_activation_post_process(node_obj):
                if len(node.args) != 1:
                    raise AssertionError(
                        f"Expected node.args to have length 1, got {len(node.args)}"
                    )
                if not isinstance(node.args[0], Node):
                    raise AssertionError(f"Expected Node, got {type(node.args[0])}")
                node = node.args[0]
    return node