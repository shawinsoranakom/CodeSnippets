def _do_quant(
        self,
        x: torch.Tensor | tuple[torch.Tensor, torch.Tensor],
        a1_dtype: torch.dtype,
        quant_config: FusedMoEQuantConfig,
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        if self.use_fp8_dispatch:
            block_k = (
                quant_config.block_shape[1]
                if quant_config.block_shape is not None
                else None
            )
            if block_k == NIXL_EP_QUANT_BLOCK_SIZE:
                # NIXL EP kernels did the quantization for us.
                x, x_scales = x
                return x, x_scales

            # Dequant to get back the tokens in the datatype we dispatched in.
            x_fp8, x_scales = x
            x = dequant_fp8(x_fp8, x_scales).to(dtype=a1_dtype)

        assert isinstance(x, torch.Tensor)

        num_experts, max_tokens, hidden_dim = x.size()

        x = x.view((-1, hidden_dim))
        q_dtype = quant_config.quant_dtype

        if envs.VLLM_FLASHINFER_MOE_BACKEND == "masked_gemm":
            logger.info_once(
                "Skip quantization when using FlashInfer CUTEDSL(masked_gemm) "
                "for ModelOptNvFp4FusedMoE."
            )
            q_dtype = None

        x, x_scales = moe_kernel_quantize_input(
            x,
            quant_config.a1_scale,
            q_dtype,
            quant_config.per_act_token_quant,
            quant_config.block_shape,
        )
        x = x.view((num_experts, -1, hidden_dim))

        if q_dtype is not None:
            assert x_scales is not None
            x_scales = normalize_batched_scales_shape(x_scales, num_experts)

        return x, x_scales