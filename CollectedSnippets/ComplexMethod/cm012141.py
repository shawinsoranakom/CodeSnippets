def __init__(self) -> None:
        super().__init__()

        self.default_num_stages = get_backend_num_stages()

        self.mm_configs: list[BaseConfig] = [
            ROCmGemmConfig(
                16, 16, 256, self.default_num_stages, 4, group_m=4, waves_per_eu=2
            ),
            ROCmGemmConfig(32, 16, 256, self.default_num_stages, 4, group_m=4),
            ROCmGemmConfig(
                32, 32, 16, self.default_num_stages, 4, group_m=8, waves_per_eu=2
            ),
            ROCmGemmConfig(32, 32, 128, self.default_num_stages, 4, group_m=8),
            ROCmGemmConfig(32, 64, 64, self.default_num_stages, 4, group_m=8),
            ROCmGemmConfig(
                64, 16, 128, self.default_num_stages, 4, group_m=8, waves_per_eu=2
            ),
            ROCmGemmConfig(64, 32, 32, self.default_num_stages, 4, group_m=8),
            ROCmGemmConfig(64, 32, 64, self.default_num_stages, 4, group_m=8),
            ROCmGemmConfig(64, 32, 64, self.default_num_stages, 8, group_m=8),
            ROCmGemmConfig(64, 32, 128, self.default_num_stages, 4, group_m=8),
            ROCmGemmConfig(64, 64, 16, self.default_num_stages, 4, group_m=8),
            ROCmGemmConfig(64, 64, 64, self.default_num_stages, 4, group_m=4),
            ROCmGemmConfig(64, 64, 128, self.default_num_stages, 8, group_m=16),
            ROCmGemmConfig(64, 64, 256, self.default_num_stages, 8, group_m=4),
            ROCmGemmConfig(
                64, 128, 32, self.default_num_stages, 4, group_m=4, waves_per_eu=2
            ),
            ROCmGemmConfig(64, 128, 32, self.default_num_stages, 8, group_m=8),
            ROCmGemmConfig(64, 128, 64, self.default_num_stages, 8, group_m=4),
            ROCmGemmConfig(64, 128, 128, self.default_num_stages, 8, group_m=4),
            ROCmGemmConfig(128, 32, 32, self.default_num_stages, 4, group_m=8),
            ROCmGemmConfig(128, 32, 64, self.default_num_stages, 4, group_m=8),
            ROCmGemmConfig(
                128, 64, 32, self.default_num_stages, 4, group_m=8, waves_per_eu=2
            ),
            ROCmGemmConfig(128, 64, 64, self.default_num_stages, 4, group_m=16),
            ROCmGemmConfig(128, 64, 128, self.default_num_stages, 8, group_m=4),
            ROCmGemmConfig(
                128, 128, 32, self.default_num_stages, 4, group_m=16, waves_per_eu=2
            ),
            ROCmGemmConfig(128, 128, 32, self.default_num_stages, 8, group_m=16),
            ROCmGemmConfig(
                128, 128, 32, self.default_num_stages, 8, group_m=16, waves_per_eu=2
            ),
            ROCmGemmConfig(128, 128, 64, self.default_num_stages, 4, group_m=16),
            ROCmGemmConfig(128, 128, 64, self.default_num_stages, 8, group_m=8),
            ROCmGemmConfig(128, 128, 128, self.default_num_stages, 8, group_m=16),
            ROCmGemmConfig(
                128, 256, 32, self.default_num_stages, 4, group_m=16, waves_per_eu=2
            ),
            ROCmGemmConfig(128, 256, 64, self.default_num_stages, 8, group_m=4),
            ROCmGemmConfig(256, 64, 64, self.default_num_stages, 8, group_m=4),
            ROCmGemmConfig(
                256, 128, 32, self.default_num_stages, 4, group_m=4, waves_per_eu=2
            ),
            ROCmGemmConfig(256, 128, 32, self.default_num_stages, 8, group_m=16),
            ROCmGemmConfig(256, 128, 64, self.default_num_stages, 8, group_m=4),
            ROCmGemmConfig(256, 256, 64, self.default_num_stages, 8, group_m=4),
        ]

        # Exhaustive search for mm configs
        self.exhaustive_configs: list[BaseConfig] = [
            ROCmGemmConfig(
                BLOCK_M,
                BLOCK_N,
                BLOCK_K,
                num_stages,
                num_warps,
                group_m=group_m,
                matrix_instr_nonkdim=matrix_instr_nonkdim,
                waves_per_eu=waves_per_eu,
                kpack=kpack,
            )
            for BLOCK_M, BLOCK_N, BLOCK_K in itertools.product(
                [16, 32, 64, 128, 256], repeat=3
            )
            for num_stages in [1, self.default_num_stages]
            for num_warps in [4, 8]
            for group_m in [4, 8, 16]
            for matrix_instr_nonkdim in [0, 16]
            for waves_per_eu in [0, 2]
            for kpack in [1, 2]
        ]

        # Architecture-aware default kpack for flex configs
        default_kpack = get_default_kpack()

        self.default_flex_config = {
            (torch.float32, 64): ROCmFlexConfig(128, 32, 1, 4, kpack=default_kpack),
            (torch.float32, 128): ROCmFlexConfig(128, 32, 1, 4, kpack=default_kpack),
            (torch.float32, 256): ROCmFlexConfig(64, 16, 1, 4, kpack=default_kpack),
            (torch.bfloat16, 64): ROCmFlexConfig(128, 64, 2, 4, kpack=default_kpack),
            (torch.bfloat16, 128): ROCmFlexConfig(128, 64, 2, 4, kpack=default_kpack),
            (torch.bfloat16, 256): ROCmFlexConfig(32, 64, 2, 4, kpack=default_kpack),
            (torch.float16, 64): ROCmFlexConfig(128, 64, 2, 4, kpack=default_kpack),
            (torch.float16, 128): ROCmFlexConfig(128, 64, 2, 4, kpack=default_kpack),
            (torch.float16, 256): ROCmFlexConfig(32, 64, 2, 4, kpack=default_kpack),
        }

        self.flex_attn_fwd_autotune_configs: list[FlexConfig] = [
            ROCmFlexConfig(BLOCK1, BLOCK2, 1, w, kpack=default_kpack)
            for BLOCK1 in [16, 64, 128]
            for BLOCK2 in [16, 32, 64, 128]
            for w in [4, 8]
        ]

        self.flex_attn_bwd_autotune_configs: list[FlexBwDConfig] = [
            # See Note: flex bwd configs
            ROCmFlexBwDConfig(
                BLOCK1, BLOCK2, BLOCK2, BLOCK1, 1, w, mfma, kpack=default_kpack
            )
            for BLOCK1 in [16, 32, 64]
            for BLOCK2 in [32, 64, 128]
            for w in ([4, 8] if BLOCK1 >= 128 or BLOCK2 >= 128 else [4])
            for mfma in [0, 16]
            if BLOCK2 % BLOCK1 == 0
        ]

        self.flex_decode_autotune_configs: list[FlexDecodeConfig] = [
            ROCmFlexDecodeConfig(32, 1, 4, kpack=default_kpack),
            ROCmFlexDecodeConfig(64, 1, 4, kpack=default_kpack),
            ROCmFlexDecodeConfig(128, 1, 4, kpack=default_kpack),
            ROCmFlexDecodeConfig(32, 1, 8, kpack=default_kpack),
            ROCmFlexDecodeConfig(64, 1, 8, kpack=default_kpack),
            ROCmFlexDecodeConfig(128, 1, 8, kpack=default_kpack),
        ]

        self.exhaustive_flex_attn_fwd_configs: list[FlexConfig] = [
            ROCmFlexConfig(BLOCK_M, BLOCK_N, num_stages, num_warps, mfma, wpeu, kpack)
            for BLOCK_M in [16, 32, 64, 128]
            for BLOCK_N in [32, 64, 128]
            for num_stages in [1, 2]
            for num_warps in [2, 4, 8]
            for mfma in [0, 16]
            for wpeu in [0, int(8 // num_warps)]
            for kpack in [1, 2]
        ]

        self.exhaustive_flex_attn_bwd_configs: list[FlexBwDConfig] = [
            # See Note: flex bwd configs
            ROCmFlexBwDConfig(
                BLOCK_M1,
                BLOCK_N1,
                BLOCK_M2,
                BLOCK_N2,
                num_stages,
                num_warps,
                mfma,
                wpeu,
                kpack,
            )
            for BLOCK_M1 in [16, 32, 64, 128]
            for BLOCK_N1 in [16, 32, 64, 128]
            for BLOCK_M2 in [16, 32, 64, 128]
            for BLOCK_N2 in [16, 32, 64, 128]
            for num_stages in [1, 2]
            for num_warps in [2, 4, 8]
            for mfma in [0, 16]
            for wpeu in [0, int(8 // num_warps)]
            for kpack in [1, 2]
            if BLOCK_N1 % BLOCK_M1 == 0
            and BLOCK_M2 % BLOCK_N2 == 0  # kernel static assertions
        ]

        self.exhaustive_flex_decode_configs: list[FlexDecodeConfig] = [
            ROCmFlexDecodeConfig(
                block_n, num_stages, num_warps, mfma, wpeu, kpack=kpack
            )
            for block_n in [16, 32, 64, 128]
            for num_stages in [1, 2]
            for num_warps in [2, 4, 8]
            for mfma in [0, 16]
            for wpeu in [0, int(8 // num_warps)]
            for kpack in [1, 2]
        ]