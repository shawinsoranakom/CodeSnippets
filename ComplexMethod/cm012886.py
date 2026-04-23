def scale_weight_node(
    node: Node,
    modules: dict[str, nn.Module],
    equalization_scale: torch.Tensor,
    next_equalization_scale: torch.Tensor | None,
) -> None:
    """Scale the weights for input-weight equalization by multiplying the
    weight by 1/equalization_scale and next_equalization_scale

    Args:
        node: Current node whose weights we want to scale
        equalization_scale: Current node's calculated equalization scale
        next_equalization_scale: Next node's calculated equalization scale if
           the following node needs to be equalized, 1 otherwise
    """
    if equalization_scale is None:
        return

    if fused_module_supports_equalization(modules[str(node.target)]):
        op_module = modules[str(node.target)][0]  # type: ignore[index]
    else:
        op_module = modules[str(node.target)]
    if not (
        nn_module_supports_equalization(op_module)
        or custom_module_supports_equalization(op_module)
    ):
        raise AssertionError(
            "Expected operation module to support equalization (nn or custom)"
        )

    # Scale the weights for input-weight equalization
    # If the following layer needs to be equalized then we will multiply its scale
    weight = op_module.weight
    if not isinstance(weight, torch.Tensor):
        raise AssertionError("Expected op_module.weight to be a torch.Tensor")

    # Scale the weights by the reciprocal of the equalization scale
    # Reshape the equalization scale so that we can multiply it to the weight along axis=1
    equalization_scale_reshaped = reshape_scale(equalization_scale, 1, weight)
    scaled_weight = torch.mul(weight, torch.reciprocal(equalization_scale_reshaped))

    if next_equalization_scale is None:
        op_module.weight = nn.Parameter(scaled_weight)
        return

    # Multiply the weights row wise by the next equalization scale
    # Reshape the equalization scale so that we can multiply it to the weight along axis=0
    next_equalization_scale_reshaped = reshape_scale(next_equalization_scale, 0, weight)
    scaled_weight = torch.mul(scaled_weight, next_equalization_scale_reshaped)

    op_module.weight = nn.Parameter(scaled_weight)

    # Multiply the bias element wise by the next equalization scale
    bias = op_module.bias
    if bias is None:
        return
    if not isinstance(bias, torch.Tensor):
        raise AssertionError("Expected op_module.bias to be a torch.Tensor")

    # Reshape the equalization scale so that we can multiply it element-wise to the bias
    next_equalization_scale_reshaped = reshape_scale(next_equalization_scale, 0, bias)
    scaled_bias = torch.mul(bias, next_equalization_scale_reshaped)
    op_module.bias = nn.Parameter(scaled_bias)