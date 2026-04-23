def __init__(
        self,
        ddp_cache_data: Iterable[tuple[torch.Tensor | None, ...]] | None = None,
        config: PreTrainedConfig | None = None,
        offloading: bool = False,
        offload_only_non_sliding: bool = False,
    ):
        layers = []
        # If a config is passed, use it to infer the layer types and initialize accordingly
        if config is not None:
            decoder_config = config.get_text_config(decoder=True)
            sliding_window = getattr(decoder_config, "sliding_window", None) or getattr(
                decoder_config, "attention_chunk_size", None
            )
            layer_types = getattr(decoder_config, "layer_types", None)
            if layer_types is None:
                layer_types = []
                for _ in range(decoder_config.num_hidden_layers):
                    if sliding_window is not None:
                        layer_types.append("sliding_attention")
                    else:
                        layer_types.append("full_attention")
            # Some models have shared layers thus no cache is needed for them (e.g. Gemma3n)
            if hasattr(decoder_config, "num_kv_shared_layers"):
                layer_types = layer_types[: -decoder_config.num_kv_shared_layers]

            for layer_type in layer_types:
                # From a cache point of view, both sliding and chunked are the same in how they should behave and how many
                # states they should return - only the mask changes to make them different at the end!
                if layer_type in ("sliding_attention", "chunked_attention"):
                    layers.append(DynamicSlidingWindowLayer(sliding_window=sliding_window))
                # Note: we want moe layers to be LinearAttentionLayer, so that we can correctly grab sequence length etc from attention layers.
                # Since moe layers will stay empty (they don't need any cache), we don't want them to collide for mask creation etc
                # TODO: maybe use a dummy layer in those cases, or a dictionary {idx: Layer} for self.layers, so that we can skip
                # the indices we don't need
                elif layer_type in ("mamba", "conv", "linear_attention", "moe"):
                    layers.append(LinearAttentionLayer())
                elif layer_type == "hybrid":
                    layers.append(LinearAttentionAndFullAttentionLayer())
                else:
                    layers.append(DynamicLayer())

        # In this case, use the passed data to already fill in the Cache
        if ddp_cache_data is not None:
            # Init all the layers with the data
            for layer_idx, kv_and_optional_sliding in enumerate(ddp_cache_data):
                # If the config was not passed above, initialize a new cache layer for each entry of the ddp_data
                if config is None:
                    # kv_and_optional_sliding contains at least two elements: the key and value states. It can also
                    # contain a third element, which is an optional sliding window tensor.
                    sliding_window_tensor = kv_and_optional_sliding[2] if len(kv_and_optional_sliding) == 3 else None
                    # If there is a sliding window tensor, use it to initialize the layer
                    if sliding_window_tensor is not None:
                        # Since the same layer is dispatched across replicas, sliding_window is the same for all
                        sliding_window = sliding_window_tensor[0].item()
                        layers.append(DynamicSlidingWindowLayer(sliding_window=sliding_window))
                    else:
                        layers.append(DynamicLayer())
                # Update the layer with the data
                _, _ = layers[layer_idx].update(kv_and_optional_sliding[0], kv_and_optional_sliding[1])

        # If neither of config nor ddp_data was passed, then simply lazy init a full cache of DynamicLayer
        if len(layers) == 0:
            super().__init__(
                layer_class_to_replicate=DynamicLayer,
                offloading=offloading,
                offload_only_non_sliding=offload_only_non_sliding,
            )
        else:
            super().__init__(layers=layers, offloading=offloading, offload_only_non_sliding=offload_only_non_sliding)