def _is_qconfig_supported_by_dtype_configs(
    qconfig: QConfig, dtype_configs: list[DTypeConfig]
):
    for dtype_config in dtype_configs:
        is_dynamic = dtype_config.is_dynamic
        if is_dynamic is None:
            is_dynamic = False
        input_dtype = dtype_config.input_dtype or torch.float
        weight_dtype = dtype_config.weight_dtype or torch.float
        bias_dtype = dtype_config.bias_dtype or torch.float
        output_dtype = dtype_config.output_dtype or torch.float
        (
            qconfig_activation_dtype,
            qconfig_weight_dtype,
            qconfig_input_act_is_dynamic,
        ) = get_qconfig_dtypes(qconfig)
        qconfig_bias_dtype = (
            torch.float16
            if (
                qconfig_activation_dtype == torch.float16
                and qconfig_weight_dtype == torch.float16
                and not is_dynamic
            )
            else torch.float
        )

        if is_dynamic:
            is_match = (
                qconfig_input_act_is_dynamic
                and input_dtype == qconfig_activation_dtype
                and output_dtype == torch.float
                and weight_dtype == qconfig_weight_dtype
            )
        else:
            is_match = (
                input_dtype == qconfig_activation_dtype
                and output_dtype == qconfig_activation_dtype
                and weight_dtype == qconfig_weight_dtype
                and bias_dtype == qconfig_bias_dtype
            )
        if is_match:
            return True
    return False