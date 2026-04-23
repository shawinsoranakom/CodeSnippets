def _autograd_grad(
    outputs: Sequence[torch.Tensor],
    inputs: Sequence[torch.Tensor],
    grad_outputs: Sequence[torch.Tensor] | None = None,
    retain_graph: bool = False,
    create_graph: bool = True,
) -> tuple[torch.Tensor, ...]:
    if grad_outputs is None:
        diff_outputs = tuple(out for out in outputs if out.requires_grad)
    else:
        result = tuple(
            (out, go) for out, go in zip(outputs, grad_outputs) if out.requires_grad
        )
        if len(result) == 0:
            diff_outputs, grad_outputs = (), ()
        else:
            diff_outputs, grad_outputs = zip(*result)
    if len(diff_outputs) == 0:
        return tuple(torch.zeros_like(inp) for inp in inputs)
    with torch._dynamo.compiled_autograd._disable():
        grad_inputs = torch.autograd.grad(
            diff_outputs,
            inputs,
            grad_outputs,
            retain_graph=retain_graph,
            create_graph=create_graph,
            allow_unused=True,
        )
    grad_inputs = tuple(
        torch.zeros_like(inp) if gi is None else gi
        for gi, inp in zip(grad_inputs, inputs)
    )
    return grad_inputs