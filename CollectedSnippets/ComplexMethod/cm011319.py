def stage_backward_input(
    stage_outputs_or_loss: list[torch.Tensor],
    output_grads: list[torch.Tensor] | None,
    input_values: list[torch.Tensor],
    weights: Iterator[Parameter],
) -> tuple[tuple[torch.Tensor | None, ...], list[dict[str, Any]]]:
    """
    Compute the gradients for only the stage inputs with
    respect to the stage outputs (if non-last stage) or loss (if last stage)

    After computing input gradients, we save the intermediate nodes in `param_groups`
    for later use in stage_backward_weight. We don't need to save any other intermediate nodes
    that aren't needed for dW because when we do dW calculation, we start from saved intermediates.
    Detaching the stage_outputs_or_loss at the end of this function is important as
    it frees up the memory that the autograd graph is anticipating to be used later (but doesn't actually need).
    """
    stage_output_grad_fns: list[Node] = list(
        filter(None, map(_get_grad_fn_or_grad_acc, stage_outputs_or_loss))
    )
    stage_input_grad_fns: list[Node] = list(
        filter(None, map(_get_grad_fn_or_grad_acc, input_values))
    )
    weight_grad_fns: list[Node] = list(
        filter(None, map(_get_grad_fn_or_grad_acc, weights))
    )

    reverse_edges_dict = construct_reverse_graph(stage_output_grad_fns)
    param_groups = get_param_groups(
        stage_input_grad_fns, weight_grad_fns, reverse_edges_dict
    )

    handles = []
    for param_group in param_groups:
        for i, intermediate in enumerate(param_group["intermediates"]):

            def get_hook(param_group, i):
                def hook(grad_inputs):
                    if param_group.get("grads", None) is None:
                        param_group["grads"] = [None] * len(
                            param_group["intermediates"]
                        )
                    param_group["grads"][i] = grad_inputs

                return hook

            # These are always "split" nodes that we need to recompute, so
            # save their inputs.
            handle = intermediate.register_prehook(get_hook(param_group, i))
            handles.append(handle)

    if output_grads is None:
        # In case this is the loss and there are no output_grads, then we just use 1s
        output_grads = [
            torch.ones_like(stage_output) for stage_output in stage_outputs_or_loss
        ]

    dinputs = _autograd_grad_for_inputs(
        stage_outputs_or_loss,
        input_values,
        output_grads,
        retain_graph=True,
    )

    # Accumulate into .grad
    for inp, dinput in zip(input_values, dinputs):
        if isinstance(inp, torch.Tensor) and dinput is not None:
            if inp.grad is None:
                inp.grad = dinput
            else:
                inp.grad += dinput

    # stage_outputs_or_loss are not used in backwards after this point, so we can safely remove it from the autograd graph
    # this allows autograd to clear up the graph dedicated for this tensor and free up significant memory
    for t in stage_outputs_or_loss:
        t.detach_()

    # hooks are no longer necessary, clean up for consistency
    for handle in handles:
        handle.remove()

    return dinputs, param_groups