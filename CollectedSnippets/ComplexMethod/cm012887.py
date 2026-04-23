def scale_weight_functional(
    op_node: Node,
    model: GraphModule,
    modules: dict[str, nn.Module],
    equalization_scale: torch.Tensor,
    next_equalization_scale: torch.Tensor | None,
) -> None:
    """Scales the weight value for functional layers"""
    if equalization_scale is None:
        return

    # From the given op_node, the path looks like:
    #   get_attr(weight) -> weight_quant_obs -> weight_eq_obs -> op_node
    # So we want to trace back from the op_node to get the equalization observer
    # node, then the quantization observer node, and then finally the weight
    # node which contains the weight values.

    # Get the equalization observer node
    weight_eq_obs_node = maybe_get_weight_eq_obs_node(op_node, modules)
    if weight_eq_obs_node is None:
        return

    # Get the quantization observer node
    weight_quant_obs_node = weight_eq_obs_node.args[0]
    if weight_quant_obs_node is None:
        return
    if not (
        isinstance(weight_quant_obs_node, Node)
        and isinstance(modules[str(weight_quant_obs_node.target)], ObserverBase)
    ):
        raise AssertionError(
            "Expected weight_quant_obs_node to be a Node whose module is an ObserverBase"
        )

    # Get the get_attr(weight) node
    weight_node = weight_quant_obs_node.args[0]
    if weight_node is None:
        return
    if not (isinstance(weight_node, Node) and weight_node.op == "get_attr"):
        raise AssertionError("Expected weight node to be a 'get_attr' Node")

    weight_parent_name, weight_name = _parent_name(weight_node.target)
    weight = getattr(modules[weight_parent_name], weight_name)

    # Scale the weights for input-weight equalization
    # If the following layer needs to be equalized then we will multiply its scale
    # Reshape the equalization scale so that we can multiply it to the weight along axis=1
    equalization_scale_reshaped = reshape_scale(equalization_scale, 1, weight)
    scaled_weight = torch.mul(weight, torch.reciprocal(equalization_scale_reshaped))

    if next_equalization_scale is None:
        setattr(modules[weight_parent_name], weight_name, scaled_weight)
        return

    # Multiply the weights row wise by the next equalization scale
    # Reshape the equalization scale so that we can multiply it to the weight along axis=1
    next_equalization_scale_reshaped = reshape_scale(
        next_equalization_scale, 0, scaled_weight
    )
    scaled_weight = torch.mul(scaled_weight, next_equalization_scale_reshaped)

    setattr(modules[weight_parent_name], weight_name, scaled_weight)
    if not torch.allclose(model.get_buffer(str(weight_node.target)), scaled_weight):
        raise AssertionError("Model buffer for weight does not match the scaled weight")

    # Multiply the bias element wise by the next equalization scale
    bias_node = None
    for node in op_node.args:
        # Find the node containing the weight values
        if isinstance(node, Node) and node.op == "get_attr" and "bias" in node.name:
            bias_node = node
            break
    if bias_node is None:
        return

    bias_parent_name, bias_name = _parent_name(bias_node.target)
    bias = getattr(modules[bias_parent_name], bias_name)

    # Reshape the equalization scale so that we can multiply it element-wise to the bias
    next_equalization_scale_reshaped = reshape_scale(next_equalization_scale, 0, bias)
    scaled_bias = torch.mul(bias, next_equalization_scale_reshaped)
    setattr(modules[bias_parent_name], bias_name, scaled_bias)