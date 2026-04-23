def stage_backward_weight(
    weights: Iterator[Parameter], param_groups: list[dict[str, Any]], retain_graph=False
) -> tuple[torch.Tensor | None, ...]:
    # map weights to param_group_weights
    grad_acc_to_weight = {}
    weight_grads: list[torch.Tensor | None] = []
    for index, weight in enumerate(weights):
        grad_acc = _get_grad_fn_or_grad_acc(weight)
        grad_acc_to_weight[grad_acc] = weight, index
        weight_grads.append(weight.grad)

    for param_group in param_groups:
        valid_edges = []
        valid_grad_outputs: list[torch.Tensor] = []

        for grads_tuple, intermediate in zip(
            param_group["grads"], param_group["intermediates"]
        ):
            for i, grad in enumerate(grads_tuple):
                if grad is not None:
                    valid_edges.append(GradientEdge(intermediate, i))
                    # pyrefly: ignore [bad-argument-type]
                    valid_grad_outputs.append(grad)

        # Break a reference cycle caused inside stage_backward_input->get_hook->hook
        # The summarized cycle is:
        # `hook` -> cell -> param_group -> intermediates -> `hook`
        # because we install the hook function onto each of the intermediate autograd nodes.
        # We need to keep intermediates alive up until backward_weight, but we can free it now.
        del param_group["intermediates"]

        if valid_edges:  # Only call autograd.grad if we have valid gradients
            # [NEW!] Able to pass a GradientEdge to autograd.grad as output
            weights_edges = tuple(GradientEdge(w, 0) for w in param_group["params"])
            dweights = torch.autograd.grad(
                valid_edges,
                weights_edges,
                grad_outputs=valid_grad_outputs,
                retain_graph=retain_graph,
            )

            # release grad memory early after use
            del param_group["grads"]

            for grad_acc, dw in zip(param_group["params"], dweights):
                weight, index = grad_acc_to_weight[grad_acc]
                if weight.grad is None:
                    weight.grad = dw
                else:
                    weight.grad += dw
    # return grads in the original order weights were provided in
    return tuple(weight_grads)