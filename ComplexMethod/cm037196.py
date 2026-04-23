def __init__(
        self,
        num_heads: int,
        head_size: int,
        scale: float,
        num_kv_heads: int,
        alibi_slopes: list[float] | None,
        sliding_window: int | None,
        kv_cache_dtype: str,
        logits_soft_cap: float | None = None,
        attn_type: AttentionType = AttentionType.DECODER,
        kv_sharing_target_layer_name: int | None = None,
        sinks: torch.Tensor | None = None,
    ) -> None:
        self.num_heads = num_heads
        self.head_size = head_size
        self.scale = float(scale)
        self.num_kv_heads = num_kv_heads
        if alibi_slopes is not None:
            alibi_slopes = torch.tensor(alibi_slopes, dtype=torch.float32)
        self.alibi_slopes = alibi_slopes
        if sliding_window is None:
            self.sliding_window = (-1, -1)
        else:
            self.sliding_window = (sliding_window - 1, 0)
        self.window_left = (
            self.sliding_window[0] if self.sliding_window is not None else -1
        )
        self.kv_cache_dtype = kv_cache_dtype
        self.is_kvcache_nvfp4 = kv_cache_dtype == "nvfp4"
        self.fp4_data_dim = head_size // 2 if self.is_kvcache_nvfp4 else 0
        self.logits_soft_cap = logits_soft_cap
        self.kv_sharing_target_layer_name = kv_sharing_target_layer_name

        self.num_queries_per_kv = self.num_heads // self.num_kv_heads

        if attn_type != AttentionType.DECODER:
            raise NotImplementedError(
                "Encoder self-attention and "
                "encoder/decoder cross-attention "
                "are not implemented for "
                "FlashInferImpl"
            )

        self.sinks: torch.Tensor | None = None
        if sinks is not None:
            if sinks.shape[0] != num_heads:
                raise ValueError(
                    "Sinks must have the same number of heads as the number of "
                    f"heads in the layer. Expected {num_heads}, but got "
                    f"{sinks.shape[0]}."
                )
            self.sinks = sinks

        self.support_trtllm_attn = can_use_trtllm_attention(num_heads, num_kv_heads)
        vllm_config = get_current_vllm_config_or_none()
        self.supports_quant_query_input = (
            self.support_trtllm_attn
            and vllm_config is not None
            and not vllm_config.attention_config.disable_flashinfer_q_quantization
        )
        self.bmm1_scale: float | None = None
        self.bmm2_scale: float | None = None
        self.o_sf_scale: float | None = None

        dcp_a2a = (
            vllm_config is not None
            and vllm_config.parallel_config.decode_context_parallel_size > 1
            and vllm_config.parallel_config.dcp_comm_backend == "a2a"
        )
        if dcp_a2a:
            self.dcp_combine = partial(dcp_a2a_lse_reduce, is_lse_base_on_e=False)
        else:
            self.dcp_combine = partial(cp_lse_ag_out_rs, is_lse_base_on_e=False)