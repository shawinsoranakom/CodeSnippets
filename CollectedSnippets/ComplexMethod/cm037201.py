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
        attn_type: str = AttentionType.DECODER,
        kv_sharing_target_layer_name: str | None = None,
        sinks: torch.Tensor | None = None,
    ) -> None:
        self.kv_sharing_target_layer_name = kv_sharing_target_layer_name
        self.num_heads = num_heads
        self.head_size = head_size
        self.scale = float(scale)
        if logits_soft_cap is not None and attn_type in (
            AttentionType.ENCODER,
            AttentionType.ENCODER_ONLY,
        ):
            logger.warning_once(
                "CPU_ATTN does not support logits softcap for"
                " ENCODER and ENCODER_ONLY, outputs may be slightly off"
            )
        if logits_soft_cap is None:
            logits_soft_cap = 0
        self.logits_soft_cap = logits_soft_cap

        self.num_kv_heads = num_kv_heads
        if alibi_slopes is not None:
            alibi_slopes = torch.tensor(alibi_slopes, dtype=torch.float32)
        self.alibi_slopes = alibi_slopes
        if sliding_window is None:
            self.sliding_window = (-1, -1)
        elif attn_type == AttentionType.ENCODER_ONLY:
            self.sliding_window = (sliding_window - 1, sliding_window - 1)
        else:
            self.sliding_window = (sliding_window - 1, 0)
        self.kv_cache_dtype = kv_cache_dtype
        self.num_queries_per_kv = self.num_heads // self.num_kv_heads

        if is_quantized_kv_cache(kv_cache_dtype):
            raise NotImplementedError("FP8 KV cache is unsupported in CPU_ATTN")
        self.attn_type = attn_type

        self.sinks = sinks
        if self.sinks is not None:
            assert self.sinks.shape[0] == num_heads, (
                "Sinks must have the same number of heads as the number of "
                "heads in the layer"
            )