def maybe_swap_ffn_param(
    name: str,
    param: torch.Tensor,
    loaded_weight: torch.Tensor,
    params_dict: dict[str, torch.Tensor],
    quant_config: QuantizationConfig,
) -> torch.Tensor:
    if not (quant_config and quant_config.get_name() == "gguf") or ".fc" not in name:
        return param
    # Some GGUF models have fc1 and fc2 weights swapped
    tp_size = get_tensor_model_parallel_world_size()
    output_dim = getattr(param, "output_dim", 0)
    output_size = param.size(output_dim) * tp_size
    weight_out_size = loaded_weight.size(output_dim)
    if ".fc1." in name and output_size != weight_out_size:
        new_name = name.replace(".fc1.", ".fc2.")
        param = params_dict[new_name]
    elif ".fc2." in name and output_size != weight_out_size:
        new_name = name.replace(".fc2.", ".fc1.")
        param = params_dict[new_name]
    return param