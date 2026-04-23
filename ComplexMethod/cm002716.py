def __init__(
        self,
        config: PreTrainedConfig,
        max_cache_len: int,
        offloading: bool = False,
        offload_only_non_sliding: bool = True,
        **kwargs,
    ):
        config = config.get_text_config(decoder=True)
        layer_types = getattr(config, "layer_types", None)
        # If `layer_types` is not explicitly provided, infer if the model is fully sliding
        if layer_types is None:
            if getattr(config, "sliding_window", None) is not None:
                layer_types = ["sliding_attention" for _ in range(config.num_hidden_layers)]
            elif getattr(config, "attention_chunk_size", None) is not None:
                layer_types = ["chunked_attention" for _ in range(config.num_hidden_layers)]
            else:
                layer_types = ["full_attention" for _ in range(config.num_hidden_layers)]
        # Some models have shared layers thus no cache is needed for them (e.g. Gemma3n)
        if hasattr(config, "num_kv_shared_layers"):
            layer_types = layer_types[: -config.num_kv_shared_layers]

        layers = []
        for layer_type in layer_types:
            if layer_type == "sliding_attention":
                layer = StaticSlidingWindowLayer(max_cache_len=max_cache_len, sliding_window=config.sliding_window)
            elif layer_type == "chunked_attention":
                # From a cache point of view, both sliding and chunked are the same in how they should behave and how many
                # states they should return - only the mask changes to make them different at the end!
                layer = StaticSlidingWindowLayer(
                    max_cache_len=max_cache_len, sliding_window=config.attention_chunk_size
                )
            # LinearAttention layers are static by essence - using `"moe"` as well is a trick, see the comment about it on DynamicCache
            elif layer_type in ("mamba", "conv", "linear_attention", "moe"):
                layer = LinearAttentionLayer()
            else:
                layer = StaticLayer(max_cache_len=max_cache_len)
            layers.append(layer)

        super().__init__(layers=layers, offloading=offloading, offload_only_non_sliding=offload_only_non_sliding)