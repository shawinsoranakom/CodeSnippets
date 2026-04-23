def _get_target_activation_dtype_for_node(
    node: Node,
    qconfig: QConfigAny,
    qhandler: QuantizeHandler | None,
    named_modules: dict[str, torch.nn.Module],
    backend_config: BackendConfig,
    cache_for_no_tensor_check: dict[Node, bool],
) -> dict[str, Any]:
    """
    For each op attribute in the op's input activation, output activation,
    weight, bias - returns the settings of dtype and is_dynamic we expect
    for the `quantize` call in the reference model representation, or None
    if there is no `quantize` call needed.

    For example, if we have a node corresponding to `op0` in

      x0 -> op0 -> x1

    And we want a reference quantized representation to be

      x0 -> quant_static -> dequant -> op0 -> quant_dynamic -> dequant -> x1

    Then this function will return

      {
        "input_act_obs_or_fq_ctr": MinMaxObserver.with_args(dtype=torch.quint8, is_dynamic=False),
        "output_act_obs_or_fq_ctr": MinMaxObserver.with_args(dtype=torch.quint8, is_dynamic=False),
      }

    TODO(future PR, if needed): explicitly spell out the non-Tensor
    dtypes.
    """
    args_have_no_tensors = all_node_args_have_no_tensors(
        node, named_modules, cache_for_no_tensor_check
    )
    if args_have_no_tensors:
        return {
            "input_act_obs_or_fq_ctr": None,
            "output_act_obs_or_fq_ctr": None,
        }
    # get qconfig to determine the eventual dtype of this node
    if qconfig is not None:
        act_dtype, weight_dtype, input_act_is_dynamic = get_qconfig_dtypes(qconfig)

        # Currently `QConfig` only has one `activation` field.
        # For static quantization, it is reused for both input
        # and output activation. For dynamic quantization, this
        # field is currently only used for the input activation,
        # with the output activation being in fp32.
        # In the future this may change as we add more fields
        # to the `QConfig` object.
        bias_dtype = (
            torch.float16
            if (
                act_dtype == torch.float16
                and weight_dtype == torch.float16
                and (not input_act_is_dynamic)
            )
            else torch.float
        )

        is_general_tensor_value_op = (
            qhandler is not None and qhandler.is_general_tensor_value_op()
        )

        _is_standalone_module = qhandler is not None and qhandler.is_standalone_module()

        weight_index = None
        if (
            isinstance(node, Node)
            and node.op == "call_function"
            and node.target in backend_config._pattern_complex_format_to_config
        ):
            weight_index = backend_config._pattern_complex_format_to_config[
                node.target
            ]._input_type_to_index.get("weight")

        bias_index = None
        if (
            isinstance(node, Node)
            and node.op == "call_function"
            and node.target in backend_config._pattern_complex_format_to_config
        ):
            bias_index = backend_config._pattern_complex_format_to_config[
                node.target
            ]._input_type_to_index.get("bias")

        return {
            "input_act_obs_or_fq_ctr": qconfig.activation,
            "weight_obs_or_fq_ctr": qconfig.weight,
            "bias_obs_or_fq_ctr": PlaceholderObserver.with_args(dtype=bias_dtype),
            "weight_index": weight_index,
            "bias_index": bias_index,
            "output_act_obs_or_fq_ctr": qconfig.activation,
            "reuse_input_obs_or_fq": _is_reuse_input_qconfig(qconfig),
            "input_output_share_observers": is_general_tensor_value_op,
            "_is_standalone_module": _is_standalone_module,
        }
    return copy.copy(_DEFAULT_FP32_QCONFIG_FOR_TARGET_DTYPE_INFO)