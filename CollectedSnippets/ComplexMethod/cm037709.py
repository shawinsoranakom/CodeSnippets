def __init__(
        self,
        num_heads: int,
        scale: float,
        qk_nope_head_dim: int,
        qk_rope_head_dim: int,
        v_head_dim: int,
        q_lora_rank: int | None,
        kv_lora_rank: int,
        kv_b_proj: ColumnParallelLinear,
        cache_config: CacheConfig | None = None,
        quant_config: QuantizationConfig | None = None,
        prefix: str = "",
        use_sparse: bool = False,
        indexer: object | None = None,
        **extra_impl_args,
    ):
        super().__init__()
        self.num_heads = num_heads
        self.scale = scale
        self.qk_nope_head_dim = qk_nope_head_dim
        self.qk_rope_head_dim = qk_rope_head_dim
        self.v_head_dim = v_head_dim
        self.q_lora_rank = q_lora_rank
        self.kv_lora_rank = kv_lora_rank
        self.kv_b_proj = kv_b_proj
        self.head_size = kv_lora_rank + qk_rope_head_dim
        self.layer_name = prefix
        self.indexer = indexer

        self.num_kv_heads = 1
        self.qk_head_dim = self.qk_nope_head_dim + self.qk_rope_head_dim

        if cache_config is not None:
            kv_cache_dtype = cache_config.cache_dtype
            calculate_kv_scales = cache_config.calculate_kv_scales
        else:
            kv_cache_dtype = "auto"
            calculate_kv_scales = False
        self.quant_config = quant_config

        dtype = torch.get_default_dtype()
        self.attn_backend = get_attn_backend(
            self.head_size,
            dtype,
            kv_cache_dtype,
            use_mla=True,
            use_sparse=use_sparse,
            num_heads=self.num_heads,
        )

        # FlashMLA Sparse Attention fp8 backend uses "fp8_ds_mla" kv-cache format
        # Automatically convert fp8 kv-cache format to "fp8_ds_mla"
        if (
            self.attn_backend.get_name() == "FLASHMLA_SPARSE"
            and is_quantized_kv_cache(kv_cache_dtype)
            and kv_cache_dtype != "fp8_ds_mla"
        ):
            assert cache_config is not None
            cache_config.cache_dtype = "fp8_ds_mla"
            kv_cache_dtype = "fp8_ds_mla"
            logger.info_once(
                "Using DeepSeek's fp8_ds_mla KV cache format. To use standard "
                "fp8 kv-cache format, please set `--attention-backend "
                "FLASHINFER_MLA_SPARSE`"
            )

        if (
            self.attn_backend.get_name() == "FLASHINFER_MLA_SPARSE"
            and is_quantized_kv_cache(kv_cache_dtype)
        ):
            logger.info_once(
                "Using standard fp8 KV cache format. To use DeepSeek's fp8_ds_mla "
                "KV cache format, please set `--attention-backend FLASHMLA_SPARSE`"
            )

        # Initialize KV cache quantization attributes
        self.kv_cache_dtype = kv_cache_dtype
        self.calculate_kv_scales = calculate_kv_scales
        _init_kv_cache_quant(self, quant_config, prefix)

        if (
            cache_config is not None
            and cache_config.enable_prefix_caching
            and envs.VLLM_BATCH_INVARIANT
            and (
                self.attn_backend.get_name() == "TRITON_MLA"
                or self.attn_backend.get_name() == "FLASHINFER"
            )
        ):
            logger.warning_once(
                "Disabling prefix caching for TRITON_MLA / FLASHINFER "
                "with batch invariance, as it is not yet supported.",
            )
            cache_config.enable_prefix_caching = False

        impl_cls = cast(type[MLAAttentionImpl], self.attn_backend.get_impl_cls())
        self.impl = impl_cls(  # type: ignore[assignment]  # impl_cls always returns an MLAAttentionImpl subclass
            num_heads=self.num_heads,
            head_size=self.head_size,
            scale=self.scale,
            num_kv_heads=1,
            alibi_slopes=None,
            sliding_window=None,
            kv_cache_dtype=self.kv_cache_dtype,
            logits_soft_cap=None,
            attn_type=AttentionType.DECODER,
            kv_sharing_target_layer_name=None,
            # MLA Args
            q_lora_rank=self.q_lora_rank,
            kv_lora_rank=self.kv_lora_rank,
            qk_nope_head_dim=self.qk_nope_head_dim,
            qk_rope_head_dim=self.qk_rope_head_dim,
            qk_head_dim=self.qk_nope_head_dim + self.qk_rope_head_dim,
            v_head_dim=self.v_head_dim,
            kv_b_proj=kv_b_proj,
            indexer=indexer,
            **extra_impl_args,
        )
        self.q_pad_num_heads = getattr(self.impl, "q_pad_num_heads", None)
        self.use_direct_call = not current_platform.opaque_attention_op()

        compilation_config = get_current_vllm_config().compilation_config
        if prefix in compilation_config.static_forward_context:
            raise ValueError(f"Duplicate layer name: {prefix}")
        compilation_config.static_forward_context[prefix] = self

        self.kv_cache = torch.tensor([])

        self.use_sparse = use_sparse

        vllm_config = get_current_vllm_config_or_none()
        self.dcp_a2a = (
            vllm_config is not None
            and vllm_config.parallel_config.decode_context_parallel_size > 1
            and vllm_config.parallel_config.dcp_comm_backend == "a2a"
        )

        # Initialize q/k/v range constants.
        self.q_range = torch.tensor(envs.Q_SCALE_CONSTANT, dtype=torch.float32)
        self.k_range = torch.tensor(envs.K_SCALE_CONSTANT, dtype=torch.float32)
        self.v_range = torch.tensor(envs.V_SCALE_CONSTANT, dtype=torch.float32)

        self.is_aiter_triton_fp8_bmm_enabled = rocm_aiter_ops.is_fp8bmm_enabled()

        # If kv_b_proj_weight is unquantized, quantize it to mxfp4 if supported
        self.is_aiter_triton_fp4_bmm_enabled = (
            rocm_aiter_ops.is_fp4bmm_enabled()
            and hasattr(self.kv_b_proj, "weight")
            and self.kv_b_proj.weight.dtype == torch.bfloat16
        )

        # Attributes for forward_impl method
        self._vllm_config = get_current_vllm_config()
        self._chunked_prefill_workspace_size: int | None = None
        self._decode_concat_quant_fp8_op = _DecodeConcatQuantFP8(
            static=True,
            group_shape=GroupShape.PER_TENSOR,
            compile_native=True,
        )
        self._quant_fp8_op = QuantFP8(
            static=True,
            group_shape=GroupShape.PER_TENSOR,
            compile_native=True,
        )