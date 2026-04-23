def get_flex_attn_bwd_configs(
        self, head_dim: int, dtype: Any
    ) -> list[FlexBwDConfig]:
        flex_attn_bwd_configs: list[FlexBwDConfig] = []

        if config.max_autotune:
            if config.max_autotune_flex_search_space == "EXHAUSTIVE":
                return self.exhaustive_flex_attn_bwd_configs
            flex_attn_bwd_configs += self.flex_attn_bwd_autotune_configs

        default_kpack = get_default_kpack()
        if dtype == torch.float32:
            default_config = ROCmFlexBwDConfig(
                16, 16, 16, 16, 1, 4, kpack=default_kpack
            )
        elif head_dim <= 256:
            if head_dim == 64:
                default_config = ROCmFlexBwDConfig(
                    64, 64, 64, 64, 1, 4, kpack=default_kpack
                )
            elif head_dim == 128:
                default_config = ROCmFlexBwDConfig(
                    64, 128, 128, 64, 1, 4, kpack=default_kpack
                )
            else:
                default_config = ROCmFlexBwDConfig(
                    64, 64, 64, 64, 1, 4, kpack=default_kpack
                )
        else:
            default_config = ROCmFlexBwDConfig(
                16, 16, 16, 16, 1, 4, kpack=default_kpack
            )

        if default_config not in flex_attn_bwd_configs:
            flex_attn_bwd_configs.append(default_config)

        return flex_attn_bwd_configs