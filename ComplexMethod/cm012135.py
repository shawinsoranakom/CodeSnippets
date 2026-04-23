def __init__(self) -> None:
        # Whether the heuristic is used for int8. Use this when the heuristic is int8 exclusive
        # but prefer the preprocess_mm_configs argument when it's used for both
        self.has_int8_tensor: bool = False
        # Whether to scale configs at all
        # TODO(coconutruben): remove this once mm_plus_mm and tests support scaling
        self.should_scale_configs: bool = True
        # List of dictionaries to store the kernel configs. Configs that evaluate to true
        # will be utilised on the target platform. The configs are as follows:
        # (BLOCK_M, BLOCK_N, BLOCK_K, num_stages, num_warps)
        self.mm_configs: list[BaseConfig] = [
            GemmConfig(32, 32, 16, 1, 2),
            GemmConfig(32, 32, 128, 2, 4),
            GemmConfig(32, 64, 32, 5, 8),
            GemmConfig(64, 32, 32, 5, 8),
            GemmConfig(64, 32, 128, 5, 4),
            GemmConfig(64, 64, 16, 2, 4),
            GemmConfig(64, 64, 32, 2, 4),
            GemmConfig(64, 64, 64, 3, 8),
            GemmConfig(64, 64, 128, 5, 4),
            GemmConfig(64, 128, 32, 3, 4),
            GemmConfig(64, 128, 32, 4, 8),
            GemmConfig(64, 128, 64, 3, 4),
            GemmConfig(64, 128, 128, 4, 4),
            GemmConfig(128, 64, 32, 3, 4),
            GemmConfig(128, 64, 32, 4, 8),
            GemmConfig(128, 128, 32, 2, 8),
            GemmConfig(128, 128, 32, 3, 4),
            GemmConfig(128, 128, 64, 3, 4),
            GemmConfig(128, 128, 64, 5, 8),
            GemmConfig(128, 128, 128, 4, 8),
        ]

        # Exhaustive search for mm configs
        self.exhaustive_configs: list[BaseConfig] = [
            GemmConfig(
                BLOCK_M, BLOCK_N, BLOCK_K, num_stages, num_warps, group_m=group_m
            )
            for BLOCK_M, BLOCK_N, BLOCK_K in itertools.product(
                [16, 32, 64, 128, 256], repeat=3
            )
            for num_stages in [1, 2, 3, 4, 5]
            for num_warps in [2, 4, 8]
            for group_m in [8]
        ]

        # these are only used in tuned_mm when AutoHeuristic is enabled
        # the idea is that when AutoHeuristic collects data to learn a heuristic, more configs are autotuned
        # when the learned heuristic is used, the learned heuristic reduces the number of configs down to 10
        # which saves compilation time (since less configs are autotuned) and potentially increase performance
        # because the learned heuristic might predict a config that is not part mm_configs
        self.extra_mm_configs: list[BaseConfig] = [
            GemmConfig(16, 32, 16, 3, 2),
            GemmConfig(16, 32, 32, 4, 2),
            GemmConfig(16, 32, 32, 5, 2),
            GemmConfig(64, 64, 128, 3, 4),
            GemmConfig(128, 64, 32, 2, 2),
            GemmConfig(128, 64, 64, 3, 8),
            GemmConfig(128, 64, 128, 4, 8),
            GemmConfig(128, 128, 32, 4, 4),
            GemmConfig(128, 128, 64, 3, 8),
            GemmConfig(128, 128, 64, 5, 4),
        ]

        self.int8_mm_configs: list[BaseConfig] = [
            GemmConfig(64, 64, 32, 2, 4),
            GemmConfig(64, 128, 32, 3, 4),
            GemmConfig(128, 64, 32, 3, 4),
            GemmConfig(64, 128, 32, 4, 8),
            GemmConfig(128, 64, 32, 4, 8),
            GemmConfig(64, 32, 32, 5, 8),
            GemmConfig(32, 64, 32, 5, 8),
            GemmConfig(128, 128, 32, 2, 8),
            GemmConfig(64, 64, 64, 3, 8),
            GemmConfig(128, 256, 128, 3, 8),
            GemmConfig(256, 128, 128, 3, 8),
        ]

        self.mixed_mm_configs: list[BaseConfig] = [
            GemmConfig(16, 128, 256, 3, 4),
            GemmConfig(16, 128, 256, 5, 8),
        ]

        self.persistent_mm_configs: list[BaseConfig] = [
            GemmConfig(128, 256, 64, 3, 8),
            GemmConfig(128, 128, 64, 3, 8),
            GemmConfig(128, 128, 128, 3, 8),
            GemmConfig(128, 128, 128, 3, 4),
            GemmConfig(128, 128, 64, 4, 8),
            GemmConfig(128, 128, 64, 5, 8),
            GemmConfig(256, 128, 64, 4, 8),
            GemmConfig(128, 128, 64, 5, 4),
        ]

        self.blackwell_persistent_mm_configs: list[BaseConfig] = [
            BlackwellGPUGemmConfig(
                128,
                256,
                64,
                4,
                8,
                epilogue_subtile=2,
                warp_specialize=True,
                flatten=True,
            ),
            BlackwellGPUGemmConfig(
                256,
                128,
                64,
                3,
                8,
                epilogue_subtile=2,
                warp_specialize=True,
                flatten=True,
            ),
            BlackwellGPUGemmConfig(
                128,
                256,
                128,
                2,
                8,
                epilogue_subtile=2,
                warp_specialize=True,
                flatten=True,
            ),
            BlackwellGPUGemmConfig(
                128,
                256,
                64,
                3,
                8,
                epilogue_subtile=2,
                warp_specialize=True,
                flatten=True,
            ),
            BlackwellGPUGemmConfig(
                128,
                128,
                128,
                3,
                4,
                epilogue_subtile=2,
                warp_specialize=True,
                flatten=True,
            ),
            BlackwellGPUGemmConfig(
                256,
                128,
                64,
                3,
                8,
                epilogue_subtile=2,
                warp_specialize=True,
                flatten=True,
            ),
            BlackwellGPUGemmConfig(
                128,
                128,
                128,
                3,
                8,
                epilogue_subtile=2,
                warp_specialize=True,
                flatten=True,
            ),
            # Include no-subtiling. Always required for testing.
            BlackwellGPUGemmConfig(
                256,
                128,
                64,
                3,
                8,
                epilogue_subtile=1,
                warp_specialize=True,
                flatten=True,
            ),
            BlackwellGPUGemmConfig(
                128,
                128,
                128,
                3,
                8,
                epilogue_subtile=1,
                warp_specialize=True,
                flatten=True,
            ),
            # Include subtile=4. Always required for testing.
            BlackwellGPUGemmConfig(
                256,
                128,
                64,
                4,
                8,
                epilogue_subtile=4,
                warp_specialize=True,
                flatten=True,
            ),
            BlackwellGPUGemmConfig(
                128,
                128,
                128,
                4,
                8,
                epilogue_subtile=4,
                warp_specialize=True,
                flatten=True,
            ),
        ]

        self.blackwell_persistent_addmm_configs: list[BaseConfig] = [
            # Include each subtiling factor for testing.
            BlackwellGPUGemmConfig(
                256,
                128,
                64,
                2,
                4,
                epilogue_subtile=2,
                warp_specialize=True,
                flatten=True,
            ),
            BlackwellGPUGemmConfig(
                256,
                128,
                64,
                2,
                4,
                epilogue_subtile=1,
                warp_specialize=True,
                flatten=True,
            ),
            BlackwellGPUGemmConfig(
                256,
                128,
                64,
                2,
                4,
                epilogue_subtile=4,
                warp_specialize=True,
                flatten=True,
            ),
        ]

        self.scaled_mm_configs: list[BaseConfig] = [
            GemmConfig(128, 256, 32, 3, 8),
            GemmConfig(256, 128, 32, 3, 8),
            GemmConfig(256, 64, 32, 4, 4),
            GemmConfig(64, 256, 32, 4, 4),
            GemmConfig(128, 128, 32, 4, 4),
            GemmConfig(128, 64, 32, 4, 4),
            GemmConfig(64, 128, 32, 4, 4),
            GemmConfig(128, 32, 32, 4, 4),
            GemmConfig(64, 32, 32, 5, 2),
            GemmConfig(256, 128, 128, 3, 8),
            GemmConfig(256, 64, 128, 4, 4),
            GemmConfig(64, 256, 128, 4, 4),
            GemmConfig(128, 128, 128, 4, 4),
            GemmConfig(128, 64, 64, 4, 4),
            GemmConfig(64, 128, 64, 4, 4),
            GemmConfig(128, 32, 64, 4, 4),
            GemmConfig(64, 32, 64, 5, 2),
            GemmConfig(16, 32, 32, 2, 2),
            GemmConfig(16, 64, 32, 2, 2),
            GemmConfig(16, 128, 32, 2, 4),
            GemmConfig(16, 256, 32, 2, 4),
            GemmConfig(16, 32, 64, 2, 2),
            GemmConfig(16, 64, 64, 2, 2),
            GemmConfig(16, 128, 64, 2, 4),
            GemmConfig(16, 256, 64, 2, 4),
            GemmConfig(32, 32, 32, 2, 2),
            GemmConfig(32, 64, 32, 2, 2),
            GemmConfig(32, 128, 32, 2, 4),
            GemmConfig(32, 256, 32, 2, 4),
            GemmConfig(32, 32, 64, 2, 2),
            GemmConfig(32, 64, 64, 2, 2),
            GemmConfig(32, 128, 64, 2, 4),
            GemmConfig(32, 256, 64, 2, 4),
            GemmConfig(16, 32, 32, 3, 2),
            GemmConfig(16, 64, 32, 3, 2),
            GemmConfig(16, 128, 32, 3, 4),
            GemmConfig(16, 256, 32, 3, 4),
            GemmConfig(16, 32, 64, 3, 2),
            GemmConfig(16, 64, 64, 3, 2),
            GemmConfig(16, 128, 64, 3, 4),
            GemmConfig(16, 256, 64, 3, 4),
            GemmConfig(32, 32, 32, 3, 2),
            GemmConfig(32, 64, 32, 3, 2),
            GemmConfig(32, 128, 32, 3, 4),
            GemmConfig(32, 256, 32, 3, 4),
            GemmConfig(32, 32, 64, 3, 2),
            GemmConfig(32, 64, 64, 3, 2),
            GemmConfig(32, 128, 64, 3, 4),
            GemmConfig(32, 256, 64, 3, 4),
            GemmConfig(16, 32, 32, 4, 2),
            GemmConfig(16, 64, 32, 4, 2),
            GemmConfig(16, 128, 32, 4, 4),
            GemmConfig(16, 256, 32, 4, 4),
            GemmConfig(16, 32, 64, 4, 2),
            GemmConfig(16, 64, 64, 4, 2),
            GemmConfig(16, 128, 64, 4, 4),
            GemmConfig(16, 256, 64, 4, 4),
            GemmConfig(32, 32, 32, 4, 2),
            GemmConfig(32, 64, 32, 4, 2),
            GemmConfig(32, 128, 32, 4, 4),
            GemmConfig(32, 256, 32, 4, 4),
            GemmConfig(32, 32, 64, 4, 2),
            GemmConfig(32, 64, 64, 4, 2),
            GemmConfig(32, 128, 64, 4, 4),
            GemmConfig(32, 256, 64, 4, 4),
            GemmConfig(16, 32, 32, 5, 2),
            GemmConfig(16, 64, 32, 5, 2),
            GemmConfig(16, 128, 32, 5, 4),
            GemmConfig(16, 256, 32, 5, 4),
            GemmConfig(16, 32, 64, 5, 2),
            GemmConfig(16, 64, 64, 5, 2),
            GemmConfig(16, 128, 64, 5, 4),
            GemmConfig(16, 256, 64, 5, 4),
            GemmConfig(32, 32, 32, 5, 2),
            GemmConfig(32, 64, 32, 5, 2),
            GemmConfig(32, 128, 32, 5, 4),
            GemmConfig(32, 256, 32, 5, 4),
            GemmConfig(32, 32, 64, 5, 2),
            GemmConfig(32, 64, 64, 5, 2),
            GemmConfig(32, 128, 64, 5, 4),
            GemmConfig(32, 256, 64, 5, 4),
            GemmConfig(16, 32, 32, 6, 2),
            GemmConfig(16, 64, 32, 6, 2),
            GemmConfig(16, 128, 32, 6, 4),
            GemmConfig(16, 256, 32, 6, 4),
            GemmConfig(16, 32, 64, 6, 2),
            GemmConfig(16, 64, 64, 6, 2),
            GemmConfig(16, 128, 64, 6, 4),
            GemmConfig(16, 256, 64, 6, 4),
            GemmConfig(32, 32, 32, 6, 2),
            GemmConfig(32, 64, 32, 6, 2),
            GemmConfig(32, 128, 32, 6, 4),
            GemmConfig(32, 256, 32, 6, 4),
            GemmConfig(32, 32, 64, 6, 2),
            GemmConfig(32, 64, 64, 6, 2),
            GemmConfig(32, 128, 64, 6, 4),
            GemmConfig(32, 256, 64, 6, 4),
            GemmConfig(64, 16, 256, 5, 4),
            GemmConfig(64, 32, 256, 5, 4),
            GemmConfig(64, 128, 128, 2, 4),
            GemmConfig(64, 128, 128, 3, 4),
            GemmConfig(128, 128, 128, 2, 4),
            GemmConfig(128, 256, 128, 4, 8),
            GemmConfig(256, 128, 128, 2, 4),
            GemmConfig(256, 128, 128, 2, 8),
        ]

        self.scaled_persistent_mm_configs: list[BaseConfig] = [
            GemmConfig(128, 128, 64, 3, 8),
            GemmConfig(128, 128, 128, 3, 8),
            GemmConfig(128, 128, 128, 4, 8),
            GemmConfig(128, 128, 128, 4, 4),
            GemmConfig(128, 128, 128, 3, 4),
            GemmConfig(128, 128, 128, 5, 4),
            GemmConfig(128, 128, 128, 5, 8),
            GemmConfig(128, 128, 128, 6, 8),
            GemmConfig(128, 128, 64, 4, 8),
            GemmConfig(64, 32, 256, 5, 4),
            GemmConfig(128, 256, 128, 3, 8),
            GemmConfig(64, 128, 256, 4, 4),
            GemmConfig(64, 256, 128, 4, 4),
        ]

        self.blackwell_scaled_persistent_mm_configs = [
            BlackwellGPUGemmConfig(
                block_m=c.block_m,
                block_n=c.block_n,
                block_k=c.block_k,
                num_stages=c.num_stages,
                num_warps=c.num_warps,
                hint_override=c.hint_override,
                group_m=8,
                epilogue_subtile=2,
                warp_specialize=True,
                flatten=True,
            )
            for c in self.scaled_persistent_mm_configs
        ]

        # TODO: Unify with other gemm patterns, mm_plus_mm currently follows
        # slightly different pattern than rest
        self.mm_plus_mm_configs: list[BaseConfig] = [
            GemmConfig(64, 64, 32, 2, 4),
            GemmConfig(64, 64, 32, 3, 8),
            GemmConfig(64, 64, 32, 4, 16),
            GemmConfig(64, 32, 32, 4, 8),
            GemmConfig(32, 64, 32, 4, 8),
            GemmConfig(128, 128, 32, 1, 8),
            GemmConfig(64, 64, 64, 1, 8),
            GemmConfig(32, 32, 128, 1, 8),
            GemmConfig(64, 64, 16, 2, 4),
            GemmConfig(32, 32, 16, 1, 2),
        ]

        self.conv_configs: list[BaseConfig] = [
            # BLOCK_K=16 configs
            ConvConfig(64, 256, 16, 2, 4),
            ConvConfig(256, 64, 16, 2, 4),
            ConvConfig(1024, 16, 16, 1, 8),
            # BLOCK_K=32 configs
            ConvConfig(128, 128, 32, 2, 8),
            ConvConfig(64, 64, 32, 2, 4),
            ConvConfig(64, 256, 32, 2, 8),
            ConvConfig(256, 64, 32, 2, 8),
            # BLOCK_K=64 configs
            ConvConfig(128, 128, 64, 3, 8),
            ConvConfig(64, 128, 64, 4, 4),
            ConvConfig(128, 64, 64, 4, 4),
            ConvConfig(256, 128, 64, 2, 8),
            ConvConfig(128, 256, 64, 2, 8),
            # BLOCK_K=128 configs - optimal when IN_C=128 (single iteration over channels)
            ConvConfig(128, 128, 128, 2, 8),
            ConvConfig(128, 128, 128, 3, 8),
            ConvConfig(64, 128, 128, 4, 4),
            ConvConfig(256, 128, 128, 2, 8),
            ConvConfig(128, 256, 128, 2, 8),
        ]

        # Depthwise conv1d configs: BLOCK_N x BLOCK_L x BLOCK_C tiling
        # Derived from autotuning results on H100 for depthwise conv1d
        # channels-last (NLC) layout with shape x=[3072, 128, 202]
        # Matches _nlc_autotune_configs from depthwise_conv1d_benchmark.py
        self.depthwise_conv_configs: list[DepthwiseConvConfig] = [
            # BLOCK_C=32, BLOCK_L=32
            DepthwiseConvConfig(
                block_n=16, block_l=32, block_c=32, num_stages=4, num_warps=8
            ),
            DepthwiseConvConfig(
                block_n=16, block_l=32, block_c=32, num_stages=4, num_warps=4
            ),
            DepthwiseConvConfig(
                block_n=32, block_l=32, block_c=32, num_stages=5, num_warps=8
            ),
            DepthwiseConvConfig(
                block_n=32, block_l=32, block_c=32, num_stages=4, num_warps=4
            ),
            # BLOCK_C=32, BLOCK_L=64
            DepthwiseConvConfig(
                block_n=16, block_l=64, block_c=32, num_stages=4, num_warps=8
            ),
            DepthwiseConvConfig(
                block_n=16, block_l=64, block_c=32, num_stages=4, num_warps=4
            ),
            DepthwiseConvConfig(
                block_n=32, block_l=64, block_c=32, num_stages=3, num_warps=8
            ),
            # BLOCK_C=32, BLOCK_L=256
            DepthwiseConvConfig(
                block_n=16, block_l=256, block_c=32, num_stages=5, num_warps=8
            ),
            DepthwiseConvConfig(
                block_n=16, block_l=256, block_c=32, num_stages=4, num_warps=4
            ),
            DepthwiseConvConfig(
                block_n=32, block_l=256, block_c=32, num_stages=3, num_warps=8
            ),
            # BLOCK_C=64
            DepthwiseConvConfig(
                block_n=16, block_l=32, block_c=64, num_stages=4, num_warps=8
            ),
            DepthwiseConvConfig(
                block_n=16, block_l=32, block_c=64, num_stages=4, num_warps=4
            ),
            DepthwiseConvConfig(
                block_n=16, block_l=64, block_c=64, num_stages=3, num_warps=8
            ),
            # BLOCK_C=128
            DepthwiseConvConfig(
                block_n=16, block_l=32, block_c=128, num_stages=3, num_warps=8
            ),
            DepthwiseConvConfig(
                block_n=16, block_l=32, block_c=128, num_stages=3, num_warps=4
            ),
        ]

        self.flex_attn_fwd_autotune_configs: list[FlexConfig] = [
            FlexConfig(128, 64, 3, 4),
            FlexConfig(128, 128, 3, 4),
            FlexConfig(128, 128, 2, 8),
            FlexConfig(128, 128, 1, 8),
            FlexConfig(64, 128, 3, 4),
            FlexConfig(64, 64, 3, 4),
        ]

        self.flex_attn_bwd_autotune_configs: list[FlexBwDConfig] = [
            # See Note: flex bwd configs
            FlexBwDConfig(BLOCK_M, BLOCK_N, BLOCK_N, BLOCK_M, s, w)
            for BLOCK_M in [32, 64]
            for BLOCK_N in [32, 64, 128]
            for s in [1, 3, 4, 5]  # num_stages
            for w in ([4, 8] if BLOCK_M >= 128 or BLOCK_N >= 128 else [4])
            if BLOCK_N % BLOCK_M == 0
        ]

        self.flex_decode_autotune_configs: list[FlexDecodeConfig] = [
            FlexDecodeConfig(64, 3, 2),
            FlexDecodeConfig(32, 3, 2),
            FlexDecodeConfig(128, 3, 2),
        ]

        self.exhaustive_flex_attn_fwd_configs: list[FlexConfig] = [
            FlexConfig(BLOCK_M, BLOCK_N, num_stages, num_warps)
            for BLOCK_M in [16, 32, 64, 128]
            for BLOCK_N in [32, 64, 128]
            for num_stages in [1, 3, 4, 5]
            for num_warps in [2, 4, 8]
        ]

        self.exhaustive_flex_attn_bwd_configs: list[FlexBwDConfig] = [
            # See Note: flex bwd configs
            FlexBwDConfig(BLOCK_M1, BLOCK_N1, BLOCK_M2, BLOCK_N2, num_stages, num_warps)
            for BLOCK_M1 in [16, 32, 64, 128]
            for BLOCK_N1 in [16, 32, 64, 128]
            for BLOCK_M2 in [16, 32, 64, 128]
            for BLOCK_N2 in [16, 32, 64, 128]
            for num_stages in [1, 3, 4]
            for num_warps in [2, 4, 8]
            if BLOCK_N1 % BLOCK_M1 == 0
            and BLOCK_M2 % BLOCK_N2 == 0  # kernel static assertions
        ]

        self.exhaustive_flex_decode_configs: list[FlexDecodeConfig] = [
            FlexDecodeConfig(block_n, num_stages, num_warps)
            for block_n in [16, 32, 64, 128]
            for num_stages in [1, 3, 4, 5]
            for num_warps in [2, 4, 8]
        ]