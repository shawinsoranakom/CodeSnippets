def _get_arg_as_input_act_obs_or_fq(
    arg: Node,
    node: Node,
    named_modules: dict[str, torch.nn.Module],
    obs_or_fq_map: dict[EdgeOrNode, ObserverOrFakeQuantize],
    is_qat: bool,
) -> ObserverOrFakeQuantize | None:
    """Get the observer or fake quant constructor for the Argument `arg`, as input
    to Node `node`
    """
    if not isinstance(arg, Node):
        raise AssertionError("arg must be a Node")

    if "quantization_annotation" in node.meta:
        raise NotImplementedError(
            "Please use torchao (https://github.com/pytorch/ao) for pt2e quantization flow"
        )

    # we can remove the following path in the future if fx graph mode quantization is
    # no longer used
    is_weight = node_arg_is_weight(node, arg)
    is_bias = node_arg_is_bias(node, arg)
    is_activation = not is_weight and not is_bias
    obs_or_fq_ctr = None
    if is_activation:
        obs_or_fq_ctr = node.meta["target_dtype_info"].get(
            "input_act_obs_or_fq_ctr", _DEFAULT_FP32_OBS_OR_FQ_CTR
        )
    elif is_weight:
        if node.target not in NON_QUANTIZABLE_WEIGHT_OPS:
            obs_or_fq_ctr = node.meta["target_dtype_info"].get(
                "weight_obs_or_fq_ctr", _DEFAULT_FP32_OBS_OR_FQ_CTR
            )
    else:
        obs_or_fq_ctr = node.meta["target_dtype_info"].get(
            "bias_obs_or_fq_ctr", _DEFAULT_FP32_OBS_OR_FQ_CTR
        )
    return obs_or_fq_ctr() if obs_or_fq_ctr else None