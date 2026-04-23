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
            if block_k == DEEPEP_QUANT_BLOCK_SIZE:
                # DeepEP kernels did the quantization for us.
                x, x_scales = x
                return x, x_scales

            # Dequant to get back the tokens in the datatype we dispatched in.
            x_fp8, x_scales = x
            x = dequant_fp8(x_fp8, x_scales).to(dtype=a1_dtype)

        assert isinstance(x, (torch.Tensor, tuple))
        q_dtype = quant_config.quant_dtype

        if q_dtype == "nvfp4" and envs.VLLM_DEEPEPLL_NVFP4_DISPATCH:
            logger.info_once(
                "Since VLLM_DEEPEPLL_NVFP4_DISPATCH==1, make sure "
                "using the hybrid-ep branch of DeepEP"
                "(https://github.com/deepseek-ai/DeepEP/tree/hybrid-ep)"
            )
            assert isinstance(x, tuple)
            x_scales = x[1]
            x = x[0].permute(2, 0, 1)
            num_experts, max_tokens, hidden_dim_by_2 = x.shape
            hidden_dim = hidden_dim_by_2 * 2
            logger.info_once(
                "Quantization is fused with DeepEP nvfp4 dispatch for "
                "FlashInfer CUTEDSL as VLLM_DEEPEPLL_NVFP4_DISPATCH==1"
            )
        else:
            if q_dtype == "nvfp4":
                q_dtype = None
                logger.info_once(
                    "Using DeepEP bfloat16 dispatch for FlashInfer CUTEDSL as "
                    "VLLM_DEEPEPLL_NVFP4_DISPATCH==0"
                )
            assert isinstance(x, torch.Tensor)
            num_experts, max_tokens, hidden_dim = x.size()

            # TODO (varun): Optimization - Use a batched version of quant
            x = x.view((-1, hidden_dim))
            x, x_scales = moe_kernel_quantize_input(
                x,
                quant_config.a1_scale,
                q_dtype,
                quant_config.per_act_token_quant,
                quant_config.block_shape,
            )
            x = x.view((num_experts, -1, hidden_dim))

        if q_dtype is not None and q_dtype != "nvfp4":
            assert x_scales is not None
            x_scales = normalize_batched_scales_shape(x_scales, num_experts)

        return x, x_scales