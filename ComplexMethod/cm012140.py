def get_flex_decode_configs(
        self, head_dim: int, dtype: Any
    ) -> list[FlexDecodeConfig]:
        capability = torch.cuda.get_device_capability()

        default_config = FlexDecodeConfig(64, 1, 2)

        flex_decode_configs: list[FlexDecodeConfig] = []

        if config.max_autotune:
            if config.max_autotune_flex_search_space == "EXHAUSTIVE":
                return self.exhaustive_flex_decode_configs
            flex_decode_configs += self.flex_decode_autotune_configs

        if capability in [(9, 0), (10, 0), (10, 3)]:  # sm_90, sm_100, sm_103
            if head_dim > 128 and dtype == torch.float32:
                default_config = FlexDecodeConfig(64, 1, 2)
            else:
                default_config = FlexDecodeConfig(64, 3, 2)
        if capability == (11, 0):
            default_config = FlexDecodeConfig(16, 1, 2)
        else:
            default_config = FlexDecodeConfig(64, 1, 2)

        if default_config not in flex_decode_configs:
            flex_decode_configs.append(default_config)

        return flex_decode_configs