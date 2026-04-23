def check_escaped_gradients(
    outputs: Any,
    inputs: Sequence[Any],
    requires_grad_indices: set[int],
) -> None:
    """
    Check if autograd graph depends on tensors that not passed as explicit inputs.

    Controlled by torch._dynamo.config.leaf_function_check_escaped_gradients.
    """
    if not requires_grad_indices:
        return

    import torch._dynamo.config as config

    if not config.leaf_function_check_escaped_gradients:
        return

    input_nodes: set[torch.autograd.graph.Node] = set()
    for i, inp in enumerate(inputs):
        if (
            isinstance(inp, torch.Tensor)
            and i in requires_grad_indices
            and inp.requires_grad
        ):
            edge = get_gradient_edge(inp)
            if edge.node is not None:
                input_nodes.add(edge.node)

    flat_outputs = outputs if isinstance(outputs, tuple) else (outputs,)
    start_nodes: set[torch.autograd.graph.Node] = {
        out.grad_fn
        for out in flat_outputs
        if isinstance(out, torch.Tensor)
        and out.requires_grad
        and out.grad_fn is not None
    }
    if not start_nodes:
        return

    escaped: set[torch.autograd.graph.Node] = set()
    visited: set[torch.autograd.graph.Node] = set()
    stack = list(start_nodes)

    while stack:
        node = stack.pop()
        if node in visited or node in input_nodes:
            continue
        visited.add(node)

        for next_node, _ in node.next_functions:
            if next_node is None or next_node in input_nodes:
                continue
            if not next_node.next_functions:
                escaped.add(next_node)
            else:
                stack.append(next_node)

    if escaped:
        tensor_info = []
        for node in escaped:
            if hasattr(node, "variable"):
                t = node.variable
                tensor_info.append(
                    f"  - Tensor(shape={list(t.shape)}, dtype={t.dtype})"
                )
        tensor_details = (
            "\n".join(tensor_info) if tensor_info else "  (tensor details unavailable)"
        )

        raise RuntimeError(
            f"@leaf_function detected {len(escaped)} tensor(s) with requires_grad=True "
            f"that are not passed as explicit inputs:\n{tensor_details}\n"
            f"Gradients will not flow back to closure-captured or global tensors. "
            f"Pass them as explicit arguments to the leaf function."
        )