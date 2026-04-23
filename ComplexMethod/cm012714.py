def get_cache_blocking(register_blocking, thread_blocking):
            Mr = register_blocking.block_m
            Nr = register_blocking.block_n
            Kr = register_blocking.block_k

            Mt_blocks = thread_blocking.block_m
            Nt_blocks = thread_blocking.block_n
            Kt_blocks = thread_blocking.block_k

            if config.cpp.gemm_cache_blocking is not None:
                blockings = [int(i) for i in config.cpp.gemm_cache_blocking.split(",")]
                assert len(blockings) == 3
                Mc_blocks, Nc_blocks, Kc_blocks = blockings
                return (
                    min(Mc_blocks, Mt_blocks),
                    min(Nc_blocks, Nt_blocks),
                    min(Kc_blocks, Kt_blocks),
                )

            # The ratios below are empirically determined to decide
            # the effective sizes of L1 and L2.
            # TODO: tune the factor here
            L1_limit_factor = 0.8
            L2_limit_factor = 0.5

            L1_cache_size = torch.cpu.get_capabilities().get(
                "l1d_cache_size", 0
            )  # per core cache size in Bytes
            assert L1_cache_size > 0, (
                f"Expect L1_cache_size > 0 but got {L1_cache_size}"
            )
            L1 = L1_cache_size * L1_limit_factor

            L2_cache_size = torch.cpu.get_capabilities().get(
                "l2_cache_size", 0
            )  # per core cache size in Bytes
            assert L2_cache_size > 0, (
                f"Expect L2_cache_size > 0 but got {L2_cache_size}"
            )
            L2 = L2_cache_size * L2_limit_factor

            def get_num_byte(dtype):
                return torch.tensor([], dtype=dtype).element_size()

            dtype_A = self.input_nodes[0].get_dtype()
            dtype_B = self.input_nodes[1].get_dtype()
            num_byte_A = get_num_byte(dtype_A)
            num_byte_B = get_num_byte(dtype_B)
            if dtype_A is torch.bfloat16 and dtype_B is torch.int8 and Kr != 1:
                # We will cache dequantized weights (BF16) in L1D for AMX micro-kernel.
                # In this case, the choice of the micro-kernel being used can't be decoupled from
                # the cache blocking.
                # TODO: Decouple the choice of micro-kernel from cache blocking
                num_byte_B *= num_byte_A

            # NOTE [CPP GEMM Cache Blocking Algorithm]
            # Our overall strategy is to
            # 1) Make cache blocks of B L1-reside and reused by multiple rows of A, i.e. Mc.
            #    Here, B is Kc x Nr where Nr is a single register block. We use L1 size to
            #    decide Kc. We want to make Mc large enough to better reuse B.
            # 2) Make cache blocks of A L2-reside, which would limit Mc. We want to reuse A
            #    along N, where we have two sub-strategies (see notes below) to decide Mc and Nc.

            # Step 1: Decide Kc assuming B block is L1-reside.
            size_cache_B = Kr * Kt_blocks * Nr * num_byte_B

            Kc_blocks = Kt_blocks
            if size_cache_B > L1:
                Kc_blocks = math.floor(L1 / (Kr * Nr * num_byte_B))

            if (
                config.cpp.use_small_dequant_buffer
                and dtype_A is torch.bfloat16
                and Mt_blocks == 1
            ):
                if dtype_B is torch.uint8:
                    # A16W4
                    # Make a small dequant_B buffer for woq int4 [q_group_size, Nr]
                    # Since when Mt_blocks == 1, L1-reside B block can't be reused by A.
                    if Kc_blocks * Kr >= self.q_group_size():
                        Kc_blocks = self.q_group_size() // Kr

                elif dtype_B is torch.int8:
                    # A16W8
                    # Make A, B, C buffer in L1
                    A_buf_size_div_K = self.m * num_byte_A
                    B_buf_size_div_K = Nr * num_byte_B
                    # assume acc in float32/int32 and Mc_blocks = Nc_blocks = 1
                    C_buf_size = Mr * Nr * 4
                    K_block_size = (L1 - C_buf_size) // (
                        A_buf_size_div_K + B_buf_size_div_K
                    )
                    if Kc_blocks * Kr >= K_block_size:
                        Kc_blocks = (K_block_size + Kr - 1) // Kr

            # Step 2: Decide Mc assuming A block is L2-reside.
            min_Mc_ratio = 2  # TODO(jgong5): something to tune?
            min_Mc_blocks = math.ceil(min_Mc_ratio * Mr / Nr)
            assert min_Mc_blocks >= 1
            Kt_bytes = Kt_blocks * Kr * num_byte_A
            if min_Mc_blocks * Mr * Kt_bytes < L2:
                # Strategy 1: A (Mc x Kt) resides in L2 and reused by all Nt
                # when Nc_blocks is kept 1. Mc should be large enough (>= min_Mc_blocks)
                # to reuse B (Kc x Nr) in L1. This makes C (Mc x Nr) small enough to reside
                # in L1.
                Mc_blocks = min(Mt_blocks, math.floor(L2 / (Mr * Kt_bytes)))
                Nc_blocks = 1
            else:
                # Strategy 2: Kt is too large to hold A (Mc x Kt) in L2, we reuse
                # A (Mc x Kc) in L2 by B (Kc x Nc). C (Mc x Nc) resides in L2.
                Mc_blocks = Mt_blocks
                Nc_blocks = min(math.ceil(Mc_blocks * Mr / Nr), Nt_blocks)
                Nc_bytes = Nc_blocks * Nr * 4  # assume C or acc is float32/int32
                Kc_bytes = Kc_blocks * Kr * num_byte_A
                if Mc_blocks * Mr * (Kc_bytes + Nc_bytes) > L2:
                    # The following is the solution for 4*Mc*Nc + Mc*Kc_bytes = L2,
                    # assuming Mc == Nc for good data reuse.
                    M_max = (math.sqrt(Kc_bytes * Kc_bytes + 16 * L2) - Kc_bytes) / 8
                    if M_max < Mc_blocks * Mr:
                        Mc_blocks = math.floor(M_max / Mr)
                        Nc_blocks = min(math.ceil(Mc_blocks * Mr / Nr), Nt_blocks)

            return Mc_blocks, Nc_blocks, Kc_blocks