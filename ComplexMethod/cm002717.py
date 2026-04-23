def __init__(self, *caches) -> None:
        # For dp and ddp support, if only one argument is passed, it should be an iterable of DynamicCache ddp data
        if len(caches) == 1:
            self_attention_cache_data, cross_attention_cache_data = [], []
            for combined_cache_data in caches[0]:
                if len(combined_cache_data) == 6:  # two tuple of style (self_attn_k, self_attn_v, self_attn_sliding)
                    self_attention_cache_data.append(combined_cache_data[:3])
                    cross_attention_cache_data.append(combined_cache_data[3:])
                # To support old DDP-style init, we handle the case where the tuple has no sliding window tensor
                elif len(combined_cache_data) == 4:  # two tuple of style (self_attn_k, self_attn_v)
                    self_attention_cache_data.append(combined_cache_data[:2])
                    cross_attention_cache_data.append(combined_cache_data[2:])
                else:
                    raise ValueError(f"Expected {len(combined_cache_data) = } to be 4 or 6.\n{combined_cache_data = }")
            self.self_attention_cache = DynamicCache(self_attention_cache_data)
            self.cross_attention_cache = DynamicCache(cross_attention_cache_data)
        # Otherwise, we should get two arguments, a self-attention cache and a cross-attention cache
        elif len(caches) == 2:
            if not isinstance(caches[0], Cache) or not isinstance(caches[1], Cache):
                raise TypeError(f"One of the two arguments is not a Cache: {type(caches[0]) = }, {type(caches[1]) = }")
            self.self_attention_cache = caches[0]
            self.cross_attention_cache = caches[1]
        # Error case
        else:
            raise ValueError(f"Expected 1 or 2 arguments, got {len(caches)}")

        self.is_updated = {}
        for layer_idx in range(len(self.cross_attention_cache)):
            self.is_updated[layer_idx] = bool(self.cross_attention_cache.get_seq_length(layer_idx) > 0)