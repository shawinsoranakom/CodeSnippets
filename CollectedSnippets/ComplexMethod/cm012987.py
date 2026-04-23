def _get_adjusted_next_layer_bias(
    next_layer: nn.Module, pruned_biases: Tensor, mask: Tensor
) -> nn.Parameter:
    r"""Returns new adjusted bias for the second supported module"""
    if parametrize.is_parametrized(next_layer):
        # need to access original weight
        parametrization_dict = cast(nn.ModuleDict, next_layer.parametrizations)
        weight_parameterizations = cast(
            ParametrizationList, parametrization_dict.weight
        )
        next_weight = weight_parameterizations.original
    else:
        next_weight = cast(Tensor, next_layer.weight)

    scaling_weight = next_weight[:, ~mask]
    if isinstance(next_layer, nn.Conv2d):  # checking for Conv2d
        # Propagating first layer pruned biases and calculating the new second layer bias
        # involves more steps since the Conv2d scaling weight has extra dimensions,
        # so adding bias involves broadcasting, logically:
        # for each channel k in range(oC):
        #     scaled_biases = sum(first_bias[pruned_idx] @ next_weight[k, pruned_idx, :, :].T)
        #     new_next_bias[k] = old_next_bias[k] + scaled_biases
        scaling_product = torch.matmul(
            pruned_biases.reshape(1, -1), torch.transpose(scaling_weight, 1, 2)
        )
        sum_range = list(range(len(scaling_product.shape)))[
            1:
        ]  # all but the first dimension
        scaled_biases = torch.sum(scaling_product, sum_range)
    elif isinstance(next_layer, nn.Linear):  # Linear
        scaled_biases = torch.matmul(
            pruned_biases, torch.transpose(scaling_weight, 0, 1)
        )  # recall b2_new = b1 @ w2.T + b2
    else:
        raise NotImplementedError(f"Type {type(next_layer)} not supported yet.")

    if (
        parametrize.is_parametrized(next_layer)
        and getattr(next_layer, "_bias", None) is not None
    ):  # next_layer is parametrized & has original bias ._bias
        adjusted_bias = nn.Parameter(scaled_biases + next_layer._bias)  # type: ignore[operator]
    elif (
        not parametrize.is_parametrized(next_layer) and next_layer.bias is not None
    ):  # next_layer not parametrized & has .bias
        adjusted_bias = nn.Parameter(scaled_biases + next_layer.bias)  # type: ignore[operator]
    else:  # next_layer has no bias
        adjusted_bias = nn.Parameter(scaled_biases)
    return adjusted_bias