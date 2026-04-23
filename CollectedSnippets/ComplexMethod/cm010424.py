def autograd_grad_with_gradient_info(
    output_infos: Sequence[GradientInfo | None],
    input_infos: Sequence[GradientInfo | None],
    grad_outputs: Sequence[Any] | None = None,
    retain_graph: bool | None = None,
    create_graph: bool = False,
    allow_unused: bool = False,
) -> tuple[torch.Tensor | None, ...]:
    """
    Compute gradients using GradientInfo, it additionally handles the case
    where input and output infos are None.

    Args:
        output_infos: GradientInfo for each output (None if no grad_fn),
        input_infos: GradientInfo for each input (None if not requires_grad)
        grad_outputs: Gradients w.r.t. outputs

    Returns a tuple of gradients with None for inputs that don't require grad.
    """
    filtered_output_edges = []
    filtered_grad_outputs = []
    for i, info in enumerate(output_infos):
        if info is not None and info.edge.node is not None:
            filtered_output_edges.append(info.edge)
            if grad_outputs is not None:
                filtered_grad_outputs.append(grad_outputs[i])

    filtered_input_edges = []
    filtered_input_infos = []
    input_indices = []
    for i, info in enumerate(input_infos):
        if info is not None:
            filtered_input_edges.append(info.edge)
            filtered_input_infos.append(info)
            input_indices.append(i)

    if not filtered_output_edges or not filtered_input_edges:
        return tuple(None for _ in input_infos)

    grads = torch.autograd.grad(
        outputs=filtered_output_edges,
        inputs=filtered_input_edges,
        grad_outputs=filtered_grad_outputs if grad_outputs is not None else None,
        retain_graph=retain_graph,
        create_graph=create_graph,
        allow_unused=allow_unused,
    )

    # Reconstruct full gradient tuple with Nones at proper positions.
    #
    # NB: For unused inputs that require grad, we return zeros instead of None.
    # This is necessary because during AOT tracing, we use fake_impl to determine
    # the backward graph structure. fake_impl may not accurately reflect which
    # inputs are truly used for gradients in real_impl. For example, users often
    # write fake_impl by returning torch.empty_like(input) to get the right shape
    # without actually using the input in a differentiable computation. So we must
    # be permissive and assume all inputs with requires_grad=True could need
    # gradients. When multiple invoke_leaf_function calls share an input (e.g.,
    # a module's forward + hook both receiving the same tensor), the traced
    # backward graph generates explicit add operations to accumulate their
    # gradients. At runtime, if one leaf function doesn't actually use the input,
    # autograd.grad returns None for it, and the traced add(grad1, grad2) fails
    # because one operand is None. Returning zeros ensures the add always works.
    result: list[torch.Tensor | None] = [None] * len(input_infos)
    for filtered_idx, original_idx in enumerate(input_indices):
        grad = grads[filtered_idx]
        if grad is None:
            info = filtered_input_infos[filtered_idx]
            grad = torch.empty_strided(
                info.size, info.stride, dtype=info.dtype, device=info.device
            ).zero_()
        result[original_idx] = grad

    return tuple(result)