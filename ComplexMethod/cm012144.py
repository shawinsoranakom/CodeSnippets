def __init__(self) -> None:
        super().__init__()
        self.mm_configs = self.mm_configs + [
            GemmConfig(32, 64, 128, 2, 2),
            GemmConfig(64, 64, 32, 2, 8),
        ]
        self.xpu_default_flex_config = {
            (torch.float32, 64): FlexConfig(128, 32, 1, 16),
            (torch.float32, 128): FlexConfig(128, 32, 1, 16),
            (torch.float32, 256): FlexConfig(64, 16, 1, 8),
            (torch.bfloat16, 64): FlexConfig(128, 64, 1, 16),
            (torch.bfloat16, 128): FlexConfig(128, 64, 1, 16),
            (torch.bfloat16, 256): FlexConfig(32, 64, 1, 4),
            (torch.float16, 64): FlexConfig(128, 64, 1, 16),
            (torch.float16, 128): FlexConfig(128, 64, 1, 16),
            (torch.float16, 256): FlexConfig(32, 64, 1, 4),
        }
        self.flex_attn_fwd_autotune_configs: list[FlexConfig] = [
            FlexConfig(32, 16, 2, 4),
            FlexConfig(128, 64, 2, 16),
            FlexConfig(128, 64, 2, 8),
            FlexConfig(128, 32, 2, 16),
            FlexConfig(128, 32, 2, 8),
        ]
        self.flex_attn_bwd_autotune_configs: list[FlexBwDConfig] = [
            FlexBwDConfig(32, 32, 32, 32, 2, 4),
            FlexBwDConfig(64, 64, 64, 64, 2, 4),
        ]
        self.flex_decode_autotune_configs: list[FlexDecodeConfig] = []

        if not bool(os.getenv("CI")):
            self.flex_attn_bwd_autotune_configs += [
                # See Note: flex bwd configs
                FlexBwDConfig(BLOCK1, BLOCK2, BLOCK2, BLOCK1, s, w)
                for BLOCK1 in [32, 64]
                for BLOCK2 in [32, 64, 128]
                for s in [1, 3, 4, 5]  # num_stages
                for w in ([4, 8] if BLOCK1 >= 128 or BLOCK2 >= 128 else [4])
                if BLOCK2 % BLOCK1 == 0
            ]
            self.flex_decode_autotune_configs += [
                FlexDecodeConfig(32, 1, 2),
                FlexDecodeConfig(32, 1, 1),
                FlexDecodeConfig(32, 2, 2),
                FlexDecodeConfig(32, 2, 1),
                FlexDecodeConfig(64, 1, 2),
                FlexDecodeConfig(64, 1, 1),
                FlexDecodeConfig(64, 2, 2),
                FlexDecodeConfig(64, 2, 1),
            ]