def apply_sequence_parallel(model, model_args):
    # Replace _flash_attention_forward with new_flash_attn_forward
    module = sys.modules[model.__module__]
    cp_size = model_args.get("cp_size", 1)

    set_ulysses_sequence_parallel_group(DistributedInterface().get_group(Dim.CP))

    try:
        num_attention_heads, num_key_value_heads = model.config.num_attention_heads, model.config.num_attention_heads
    except AttributeError:
        num_attention_heads, num_key_value_heads = (
            model.config.text_config.num_attention_heads,
            model.config.text_config.num_key_value_heads,
        )

    assert num_attention_heads % cp_size == 0, "num_attention_heads must be divisible by cp_size"
    assert num_key_value_heads % cp_size == 0 or cp_size % num_key_value_heads == 0, (
        "num_key_value_heads must be divisible by cp_size"
    )

    origin_attn = transformers.modeling_flash_attention_utils._flash_attention_forward
    new_flash_attention_forward = partial(
        new_flash_attn_forward,
        group=get_ulysses_sequence_parallel_group(),
        mode="ulysses",
        attn_fn=origin_attn,
        sequence_parallel_size=cp_size,
    )

    for module_name, module in list(sys.modules.items()):
        try:
            if (
                hasattr(module, "__file__")
                and "transformers" in module.__file__
                and getattr(module._flash_attention_forward, "__name__", "") == "_flash_attention_forward"
            ):
                module._flash_attention_forward = new_flash_attention_forward
                logger.info_rank0(
                    f"Replaced _flash_attention_forward in module {module_name} with new_flash_attn_forward for sequence parallel."
                )
        except (AttributeError, TypeError):
            continue