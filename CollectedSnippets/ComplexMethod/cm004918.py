def __post_init__(self, **kwargs):
        # Backward compatibility; configs expect different names for these fields when init
        # but they have to be re-names when creating/saving the config.
        self.n_groups = kwargs.pop("mamba_n_groups") if "mamba_n_groups" in kwargs else self.n_groups
        self.conv_kernel = kwargs.pop("mamba_d_conv") if "mamba_d_conv" in kwargs else self.conv_kernel
        self.expand = kwargs.pop("mamba_expand") if "mamba_expand" in kwargs else self.expand
        self.time_step_min = kwargs.pop("mamba_dt_min") if "mamba_dt_min" in kwargs else self.time_step_min
        self.time_step_max = kwargs.pop("mamba_dt_max") if "mamba_dt_max" in kwargs else self.time_step_max
        self.time_step_limit = kwargs.pop("mamba_dt_limit") if "mamba_dt_limit" in kwargs else self.time_step_limit
        self.time_step_floor = (
            kwargs.pop("mamba_dt_init_floor") if "mamba_dt_init_floor" in kwargs else self.time_step_floor
        )
        self.use_conv_bias = kwargs.pop("mamba_conv_bias") if "mamba_conv_bias" in kwargs else self.use_conv_bias
        self.chunk_size = kwargs.pop("mamba_chunk_size") if "mamba_chunk_size" in kwargs else self.chunk_size

        # Backward compatibility: convert hybrid_override_pattern to layers_block_type
        # Always pop hybrid_override_pattern from kwargs to prevent it from being set as an attribute
        if "hybrid_override_pattern" in kwargs:
            pattern = kwargs.pop("hybrid_override_pattern")
            if self.layer_types is None:
                self.layer_types = self._pattern_to_list(pattern)
        elif self.layer_types is None:
            # Default layers_block_type if not provided
            self.layer_types = ["mamba", "moe", "attention", "mlp"]

        # Note: num_hidden_layers is deprecated and ignored if layers_block_type is explicitly provided
        # It's only kept for backward compatibility when loading old configs
        if self.num_hidden_layers is not None:
            # Warn if num_hidden_layers is provided but doesn't match layers_block_type
            if len(self.layer_types) != self.num_hidden_layers:
                logger.warning(
                    f"num_hidden_layers ({self.num_hidden_layers}) is deprecated and doesn't match "
                    f"layer_types length ({len(self.layer_types)}). Using layers_block_type length."
                )

        # Backward compatibility: convert mtp_hybrid_override_pattern to mtp_layers_block_type
        # Always pop mtp_hybrid_override_pattern from kwargs to prevent it from being set as an attribute
        if self.mtp_layers_block_type is None:
            self.mtp_layers_block_type = ["attention", "moe"]

        if "mtp_hybrid_override_pattern" in kwargs:
            pattern = kwargs.pop("mtp_hybrid_override_pattern")
            if self.mtp_layers_block_type == ["attention", "moe"]:
                self.mtp_layers_block_type = self._pattern_to_list(pattern)

        # for backward compatibility
        if self.num_key_value_heads is None:
            self.num_key_value_heads = self.num_attention_heads

        super().__post_init__(**kwargs)