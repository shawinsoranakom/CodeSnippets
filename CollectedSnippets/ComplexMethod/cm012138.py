def get_flex_attn_fwd_configs(self, head_dim: int, dtype: Any) -> list[FlexConfig]:
        capability = torch.cuda.get_device_capability()
        flex_attn_fwd_configs: list[FlexConfig] = []

        if config.max_autotune:
            if config.max_autotune_flex_search_space == "EXHAUSTIVE":
                return self.exhaustive_flex_attn_fwd_configs
            flex_attn_fwd_configs += self.flex_attn_fwd_autotune_configs

        if head_dim <= 256:
            if dtype == torch.float32:
                default_config = FlexConfig(64, 64, 3, 4)
            else:
                default_config = FlexConfig(64, 64, 3, 4)
            # here we are using sm_120_default_flex_config on THOR as well
            if capability >= (11, 0):
                default_config = self.sm_120_default_flex_config.get(
                    (dtype, head_dim), default_config
                )
            elif capability >= (10, 0):
                default_config = self.sm_100_default_flex_config.get(
                    (dtype, head_dim), default_config
                )
            elif capability == (9, 0):
                default_config = self.h100_default_flex_config.get(
                    (dtype, head_dim), default_config
                )
            elif capability >= (8, 0):
                default_config = self.a100_default_flex_config.get(
                    (dtype, head_dim), default_config
                )
        else:
            if dtype == torch.float32:
                default_config = FlexConfig(32, 16, 3, 4)
            else:
                default_config = FlexConfig(64, 32, 3, 4)

        if default_config not in flex_attn_fwd_configs:
            flex_attn_fwd_configs.append(default_config)

        return flex_attn_fwd_configs