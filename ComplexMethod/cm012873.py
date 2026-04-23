def _get_output_act_obs_or_fq(
    arg: Node,
    named_modules: dict[str, torch.nn.Module],
    obs_or_fq_map: dict[EdgeOrNode, ObserverOrFakeQuantize],
    is_qat: bool,
) -> ObserverOrFakeQuantize | None:
    """Get the constructor for observer or fake quant object for
    the argument in the original graph as the output of previous node,
    skipping inserted observers

    We are assuming that the observers are inserted correctly, and the dtype for
    argument in quantized graph will match what is specified by the qconfig
    """
    if not isinstance(arg, Node):
        raise AssertionError("arg must be a Node")

    if "quantization_annotation" in arg.meta:
        raise NotImplementedError(
            "Please use torchao (https://github.com/pytorch/ao) for pt2e quantization flow"
        )

    # Custom module LSTM output is a tuple that we broke down into the internal nodes in order
    # to insert DeQuantStubs (see `_insert_dequant_stubs_for_custom_module_lstm_output`).
    # Since we modified the graph in this case, we must trace back from the args through
    # the specific nodes we added in order to reach the original LSTM node. Otherwise, we would
    # not be able to accurately detect whether this node is a consumer of custom module LSTM.
    custom_module_lstm_node = _maybe_get_custom_module_lstm_from_node_arg(
        arg, named_modules
    )
    output_act_obs_or_fq_ctr = None
    if custom_module_lstm_node is not None:
        output_act_obs_or_fq_ctr = custom_module_lstm_node.meta["target_dtype_info"][
            "output_act_obs_or_fq_ctr"
        ]
        output_act_obs_or_fq = (
            output_act_obs_or_fq_ctr() if output_act_obs_or_fq_ctr else None
        )
    elif _is_activation_post_process_node(arg, named_modules):
        observed_arg = arg.args[0]
        if not isinstance(observed_arg, Node):
            raise AssertionError("Currently we only support observing Node")

        if "quantization_annotation" in observed_arg.meta:
            raise NotImplementedError(
                "Please use torchao (https://github.com/pytorch/ao) for pt2e quantization flow"
            )

        if "target_dtype_info" not in observed_arg.meta:
            raise AssertionError("expected 'target_dtype_info' in observed_arg.meta")
        output_act_obs_or_fq_ctr = observed_arg.meta["target_dtype_info"][
            "output_act_obs_or_fq_ctr"
        ]
        output_act_obs_or_fq = (
            output_act_obs_or_fq_ctr() if output_act_obs_or_fq_ctr else None
        )
    else:
        if "target_dtype_info" in arg.meta:
            output_act_obs_or_fq_ctr = arg.meta["target_dtype_info"].get(
                "output_act_obs_or_fq_ctr", _DEFAULT_FP32_OBS_OR_FQ_CTR
            )
        else:
            output_act_obs_or_fq_ctr = _DEFAULT_FP32_OBS_OR_FQ_CTR
        output_act_obs_or_fq = (
            output_act_obs_or_fq_ctr() if output_act_obs_or_fq_ctr else None
        )

    return output_act_obs_or_fq