def _try_load_fp8_indexer_wk(name, tensor, buf, params_dict, loaded_params):
    """
    We fuse the WK and weights_proj projections, but in some checkpoints WK is stored
    in FP8 with a separate weight_scale_inv, while weights_proj is stored in BF16.
    Upcasting to BF16 during loading enables the fusion. This function loads the FP8 WK
    weights and scale, and when both are available, dequantizes to BF16 and stores into
    the fused wk_weights_proj.weight parameter.
    """
    if "indexer.wk." not in name or "wk_weights" in name:
        return False  # Weight is not an isolated WK weight for the indexer, ignore.
    is_weight = name.endswith(".weight") and tensor.dtype == torch.float8_e4m3fn
    is_scale = "weight_scale_inv" in name
    if not is_weight and not is_scale:
        return False  # WK is not in FP8 format, ignore.
    # Buffer this tensor (weight or scale) until both have arrived.
    layer_prefix = name.rsplit(".wk.", 1)[0]  # e.g. "model.layers.0.self_attn.indexer"
    entry = buf.setdefault(layer_prefix, {})
    entry["weight" if is_weight else "scale"] = tensor
    if "weight" not in entry or "scale" not in entry:
        return True  # still waiting for the other param

    # We have both weight and scale: dequantize FP8 to BF16.
    weight_fp8, scale_inv = entry["weight"], entry["scale"]
    del buf[layer_prefix]
    block_size = weight_fp8.shape[1] // scale_inv.shape[1]
    weight_bf16 = scaled_dequantize(
        weight_fp8,
        scale_inv,
        group_shape=GroupShape(block_size, block_size),
        out_dtype=torch.bfloat16,
    )

    # Load the dequantized weight into shard 0 of the fused buffer.
    fused_name = f"{layer_prefix}.wk_weights_proj.weight"
    param = params_dict[fused_name]
    param.weight_loader(param, weight_bf16, 0)
    loaded_params.add(fused_name)
    return True