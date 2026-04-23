def get_linear_quant_method(
    config: GPTQConfig | GPTQMarlinConfig,
    layer: torch.nn.Module,
    prefix: str,
    linear_method_cls: type,
):
    cloned_config = deepcopy(config)
    parallel_lm_head_quantized = (
        isinstance(layer, ParallelLMHead) and cloned_config.lm_head_quantized
    )
    if isinstance(layer, LinearBase) or parallel_lm_head_quantized:
        is_layer_quantized = is_layer_gptq_quantized(
            prefix=prefix,
            quantized_layers=cloned_config.modules_in_block_to_quantize,
            fused_mapping=cloned_config.packed_modules_mapping,
        )
        # False = skip module, None = no override, else = Positive match
        if get_dynamic_override(  # noqa: E712
            cloned_config,  # noqa: E712
            layer_name=prefix,
        ) == False or (not is_layer_quantized):  # noqa: E712
            if parallel_lm_head_quantized:
                return UnquantizedEmbeddingMethod()
            return UnquantizedLinearMethod()

        if prefix:
            # Dynamic per module/layer rules may override base config
            override_config(cloned_config, prefix=prefix)

        return linear_method_cls(cloned_config)
    return None