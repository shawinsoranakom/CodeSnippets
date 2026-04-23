def _verify_nn_module_stack(graph_module: torch.fx.GraphModule) -> None:
    """
    Perform nn_module_stack checks on the graph.
    Current constraints:
        For the top level graph:
        - populated for 'call_function', 'get_attr'
        - None for 'placeholder', 'output'
        For submodule graphs:
        - None for 'placeholder', output'

    TODO(pianpwk): make this a consistent node-level check once nn_module_stack is populated for cond submodules.
    """
    # Check top-level graph for all nodes, all graphs for placeholder & output nodes
    for i, mod in enumerate([graph_module] + list(graph_module.modules())):
        if not isinstance(mod, torch.fx.GraphModule):
            continue
        for node in mod.graph.nodes:
            if node.op in ["call_function", "get_attr"]:
                if i == 0:
                    if (
                        nn_module_stack := node.meta.get("nn_module_stack", None)
                    ) is None:
                        raise SpecViolationError(
                            f"Node {node} of type {node.op} is missing nn_module_stack metadata"
                        )
                    if not all(
                        isinstance(k, str)
                        and isinstance(v, tuple)
                        and len(v) == 2
                        and all(isinstance(x, str) for x in v)
                        for k, v in nn_module_stack.items()
                    ):
                        raise SpecViolationError(
                            f"Node {node} of type {node.op} has incorrect nn_module_stack metadata format"
                            f"expected Dict[str, Tuple[str, str]], but got {nn_module_stack}"
                        )
            elif node.op in ["placeholder", "output"]:
                if node.meta.get("nn_module_stack", None):
                    raise SpecViolationError(
                        f"Node {node} of type {node.op} contains nn_module_stack metadata, this should be None"
                    )