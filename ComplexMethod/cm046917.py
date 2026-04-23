def _fix_rope_inv_freq(model):
    """Fix inv_freq corruption caused by transformers v5 meta-device loading.

    Transformers v5 initializes models on the meta device, then
    _move_missing_keys_from_meta_to_device() (modeling_utils.py) replaces ALL
    non-persistent buffers with torch.empty_like() -- uninitialized memory.

    Vanilla transformers restores inv_freq via _init_weights() which checks for
    hasattr(module, "original_inv_freq"). Unsloth's LlamaRotaryEmbedding and
    subclasses do not have this attribute, so inv_freq stays corrupted. This
    produces wrong positional encodings and causes 5-11x higher training loss.

    This function recomputes inv_freq from the stored base and dim, applies
    any model-specific scaling, and rebuilds the cos/sin caches.

    Only runs on transformers >= 5.0.0. No-op on v4.
    """
    if not _NEEDS_ROPE_FIX:
        return model

    for name, module in model.named_modules():
        # Unsloth's LlamaRotaryEmbedding and subclasses (Extended, LinearScaling,
        # Granite). Native v5 rotary classes (Gemma3, etc.) have original_inv_freq
        # which v5's _init_weights() uses to restore inv_freq, so they are fine.
        if (
            hasattr(module, "inv_freq")
            and hasattr(module, "base")
            and hasattr(module, "dim")
            and hasattr(module, "_apply_inv_freq_scaling")
            and hasattr(module, "multi_gpu_cos_cached")
        ):
            inv_freq = 1.0 / (
                module.base
                ** (
                    torch.arange(
                        0, module.dim, 2, dtype = torch.int64, device = "cpu"
                    ).float()
                    / module.dim
                )
            )
            inv_freq = module._apply_inv_freq_scaling(inv_freq)
            module.inv_freq = inv_freq
            for device_idx in range(len(module.multi_gpu_cos_cached)):
                if module.multi_gpu_cos_cached[device_idx] is not None:
                    module._set_cos_sin_cache(
                        seq_len = module.current_rope_size,
                        device = torch.device(device_idx),
                        dtype = torch.get_default_dtype(),
                    )

        # LongRopeRotaryEmbedding (Phi-3.5 style with short_inv_freq + long_inv_freq)
        elif (
            hasattr(module, "short_inv_freq")
            and hasattr(module, "long_inv_freq")
            and hasattr(module, "base")
            and hasattr(module, "dim")
        ):
            config = getattr(model, "config", None)
            rope_scaling = getattr(config, "rope_scaling", None) if config else None
            if rope_scaling is not None:
                short_factor = rope_scaling.get("short_factor", None)
                long_factor = rope_scaling.get("long_factor", None)
                if short_factor is not None and long_factor is not None:
                    inv_freq_shape = (
                        torch.arange(
                            0, module.dim, 2, dtype = torch.int64, device = "cpu"
                        ).float()
                        / module.dim
                    )
                    sf = torch.tensor(short_factor, device = "cpu", dtype = torch.float32)
                    lf = torch.tensor(long_factor, device = "cpu", dtype = torch.float32)
                    module.short_inv_freq = 1.0 / (sf * module.base**inv_freq_shape)
                    module.long_inv_freq = 1.0 / (lf * module.base**inv_freq_shape)

                    dtype = torch.bfloat16 if is_bfloat16_supported() else torch.float16
                    t = torch.arange(
                        module.original_max_position_embeddings,
                        device = module.short_inv_freq.device,
                        dtype = torch.int64,
                    ).float()
                    freqs = torch.outer(t, module.short_inv_freq)
                    emb = torch.cat((freqs, freqs), dim = -1)
                    for device_idx in range(len(module.multi_gpu_short_cos_cached)):
                        if module.multi_gpu_short_cos_cached[device_idx] is not None:
                            device_obj = torch.device(device_idx)
                            module.multi_gpu_short_cos_cached[device_idx] = (
                                emb.cos() * module.scaling_factor
                            ).to(dtype = dtype, device = device_obj, non_blocking = True)
                            module.multi_gpu_short_sin_cached[device_idx] = (
                                emb.sin() * module.scaling_factor
                            ).to(dtype = dtype, device = device_obj, non_blocking = True)
    return model