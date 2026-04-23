def make_quant_config(
    quantization: str | None,
    w1: torch.Tensor,
    w2: torch.Tensor,
    num_experts: int,
) -> tuple[QuantizationConfig | None, QuantizedWeights]:
    from vllm.model_executor.layers.quantization.fp8 import Fp8Config

    if quantization is None:
        return None, QuantizedWeights(w13_weight=w1, w2_weight=w2)

    if quantization == "fp8":
        return Fp8Config(True), _quantize_fp8_halves(w1, w2)

    if quantization == "fp8_blocked":
        block_shape = [128, 128]
        return Fp8Config(True, weight_block_size=block_shape), _quantize_fp8_halves(
            w1, w2, block_shape
        )

    if quantization == "modelopt_fp8":
        qw = _quantize_fp8_halves(w1, w2)
        # why?
        qw.w13_input_scale = torch.ones(
            num_experts, dtype=torch.float32, device=w1.device
        )
        # why?
        qw.w2_input_scale = torch.ones(
            num_experts, dtype=torch.float32, device=w2.device
        )
        quant_config = ModelOptFp8Config(
            quant_method="FP8",
            is_checkpoint_fp8_serialized=True,
            kv_cache_quant_method=None,
            exclude_modules=[],
        )
        return quant_config, qw

    if quantization == "modelopt_fp4":
        # Quantize full w13 at once so both gate/up halves share the same
        # global scale per expert.  process_weights_after_loading uses
        # w13_weight_scale_2[:, 0] for the entire tensor, so the two shard
        # scales must match.
        w1q, w1s, w1gs = moe_quantize_weights(w1, None, "nvfp4", False, None)
        assert w1s is not None and w1gs is not None

        w2q, w2s, w2gs = moe_quantize_weights(w2, None, "nvfp4", False, None)
        assert w2s is not None and w2gs is not None

        qw = QuantizedWeights(
            w13_weight=w1q,
            w2_weight=w2q,
            w13_weight_scale=w1s,
            w2_weight_scale=w2s,
            # weight_scale_2 = 1/w_gs: the kernel computes
            # g_alphas = a_scale * w_scale_2, and correct dequant needs 1/w_gs.
            # Expand per-expert scalar to (E, 2) for the two shards.
            w13_weight_scale_2=(1.0 / w1gs).unsqueeze(1).expand(-1, 2).contiguous(),
            w2_weight_scale_2=1.0 / w2gs,
            w13_input_scale=torch.ones(
                (num_experts, 2), dtype=torch.float32, device=w1.device
            ),
            w2_input_scale=torch.ones(
                num_experts, dtype=torch.float32, device=w2.device
            ),
        )
        quant_config = ModelOptNvFp4Config(
            is_checkpoint_nvfp4_serialized=True,
            kv_cache_quant_algo=None,
            exclude_modules=[],
        )
        return quant_config, qw

    raise NotImplementedError(f"Unsupported quantization: {quantization}")