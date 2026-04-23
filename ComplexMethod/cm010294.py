def _verify_stack_trace(graph_module: torch.fx.GraphModule) -> None:
    """
    Perform stack trace checks on the graph.
    Constraints:
        - None or non-empty str for 'call_function', 'get_attr'
        - None for 'placeholder', 'output'
    """
    for mod in [graph_module, *graph_module.modules()]:
        if not isinstance(mod, torch.fx.GraphModule):
            continue
        for node in graph_module.graph.nodes:
            stack_trace = node.meta.get("stack_trace", None)
            if node.op in ["call_function", "get_attr"]:
                if not (stack_trace is None or isinstance(stack_trace, str)):
                    raise SpecViolationError(
                        f"Node {node} of type {node.op} has invalid stack_trace metadata, "
                        f"expected a string or None but instead found: {stack_trace}"
                    )
            elif node.op in ["placeholder", "output"]:
                if stack_trace:
                    raise SpecViolationError(
                        f"Node {node} of type {node.op} contains stack_trace metadata, "
                        f"expected None but instead found: {stack_trace}"
                    )