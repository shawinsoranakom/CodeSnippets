def __post_init__(self, **kwargs):
        self.qk_head_dim = self.qk_nope_head_dim + self.qk_rope_head_dim

        # MLP layer types: first 3 dense, rest sparse
        if self.mlp_layer_types is None:
            self.mlp_layer_types = ["dense"] * min(3, self.num_hidden_layers) + ["sparse"] * (
                self.num_hidden_layers - 3
            )

        # Indexer layer types
        if self.indexer_types is None:
            pattern = kwargs.pop("index_topk_pattern", None)
            freq = kwargs.pop("index_topk_freq", 1)
            if pattern is not None:
                self.indexer_types = (
                    [{"F": "full", "S": "shared"}[c] for c in pattern] if isinstance(pattern, str) else list(pattern)
                )
            else:
                # First layer full, then every freq-th layer full, rest shared
                self.indexer_types = [
                    "full" if (max(i - 1, 0) % freq) == 0 else "shared" for i in range(self.num_hidden_layers)
                ]
        PreTrainedConfig.__post_init__(self, **kwargs)