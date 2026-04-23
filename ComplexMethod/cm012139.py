def get_flex_attn_bwd_configs(
        self, head_dim: int, dtype: Any
    ) -> list[FlexBwDConfig]:
        capability = torch.cuda.get_device_capability()
        flex_attn_bwd_configs: list[FlexBwDConfig] = []
        if config.max_autotune:
            if config.max_autotune_flex_search_space == "EXHAUSTIVE":
                return self.exhaustive_flex_attn_bwd_configs
            flex_attn_bwd_configs += self.flex_attn_bwd_autotune_configs

        major, minor = capability
        if dtype == torch.float32:
            capability_class = "float32"
        elif major == 12:
            capability_class = "sm12x"
        elif major == 11:
            capability_class = "sm11x"
        elif major >= 10:
            capability_class = "sm10x"
        elif capability == (9, 0):
            capability_class = "sm90"
        elif major >= 8:
            capability_class = "sm8x"
        else:
            capability_class = "baseline"

        # fmt: off
        config_map = {
            "float32": lambda h: FlexBwDConfig(16, 16, 16, 16, 1, 4),
            "baseline": lambda h: FlexBwDConfig(16, 16, 16, 16, 1, 4),
            "sm90": lambda h: (
                FlexBwDConfig(64, 64, 64, 64, 3, 4) if h < 64 else
                FlexBwDConfig(64, 128, 128, 64, 3, 8) if h <= 128 else
                FlexBwDConfig(64, 64, 64, 64, 2, 4)
            ),
            "sm10x": lambda h: (
                FlexBwDConfig(64, 128, 128, 64, 3, 4) if h <= 128 else
                FlexBwDConfig(64, 64, 64, 64, 1, 8) if h <= 192 else
                FlexBwDConfig(64, 64, 64, 64, 1, 4)
            ),
            "sm8x": lambda h: (
                FlexBwDConfig(32, 128, 128, 32, 3, 4)
                if h < 64
                else FlexBwDConfig(
                    64, 64, 64, 64, 3 if minor == 6 and h == 128 else 2, 4
                )
            ),
            "sm11x": lambda h: (
                FlexBwDConfig(32, 128, 128, 32, 3, 4)
                if h < 64
                else FlexBwDConfig(
                    64, 64, 64, 64, 1 if h >= 128 else 2, 4
                )
            ),
            "sm12x": lambda h: (
                FlexBwDConfig(32, 128, 128, 32, 3, 4)
                if h < 64
                else FlexBwDConfig(
                    64, 64, 64, 64, 1 if h >= 128 else 2, 4
                )
            ),
        }
        # fmt: on

        if head_dim <= 256:
            default_config = config_map[capability_class](head_dim)
        else:
            default_config = FlexBwDConfig(16, 16, 16, 16, 1, 4)

        if default_config not in flex_attn_bwd_configs:
            flex_attn_bwd_configs.append(default_config)

        return flex_attn_bwd_configs