def test_fused_all_gather_scaled_matmul(
        self, gather_dim: int, scale_mode: str
    ) -> None:
        self._init_process()

        BATCH = 8
        M = 64
        N = 16
        K = 32
        group = dist.group.WORLD
        rank = self.rank

        if gather_dim == 0:
            leading_dims = (BATCH // self.world_size, M)
        elif gather_dim == 1:
            leading_dims = (BATCH, M // self.world_size)
        else:
            raise AssertionError(f"Invalid scale_mode: {scale_mode}")

        torch.manual_seed(42 + rank)

        A_shard = torch.rand(*leading_dims, K, device="cuda").to(e4m3_type)
        Bs = [torch.rand(N, K, device="cuda").to(e4m3_type).T for _ in range(3)]

        if scale_mode == "tensor-wise":
            A_scale = torch.tensor(0.1, device="cuda")
            B_scales = [torch.tensor(0.1, device="cuda") for _ in range(3)]
            out_dtypes = [None, torch.bfloat16, torch.float32]
        elif scale_mode == "row-wise-sharded":
            A_scale = torch.full((*leading_dims, 1), 0.1, device="cuda")
            B_scales = [torch.full((1, N), 0.1, device="cuda") for _ in range(3)]
            out_dtypes = [torch.bfloat16] * 3
        elif scale_mode == "row-wise-replicated":
            A_scale = torch.full((BATCH, M, 1), 0.1, device="cuda")
            B_scales = [torch.full((1, N), 0.1, device="cuda") for _ in range(3)]
            out_dtypes = [torch.bfloat16] * 3
        else:
            raise AssertionError(f"Invalid scale_mode: {scale_mode}")

        ag_output_0, mm_outputs_0 = _fused_all_gather_scaled_matmul_fallback(
            A_shard,
            Bs,
            A_scale,
            B_scales,
            gather_dim=gather_dim,
            group_name=group.group_name,
            biases=[None] * len(Bs),
            result_scales=[None] * len(Bs),
            out_dtypes=out_dtypes,
            use_fast_accum=[None] * len(Bs),
        )
        ag_output_1, mm_outputs_1 = torch.ops.symm_mem.fused_all_gather_scaled_matmul(
            A_shard,
            Bs,
            A_scale,
            B_scales,
            gather_dim=gather_dim,
            group_name=group.group_name,
            biases=[None] * len(Bs),
            result_scales=[None] * len(Bs),
            out_dtypes=out_dtypes,
            use_fast_accum=[None] * len(Bs),
        )

        self.assertTrue(
            torch.allclose(
                ag_output_0.to(torch.float32),
                ag_output_1.to(torch.float32),
            )
        )
        self.assertEqual(ag_output_0.stride(), ag_output_1.stride())
        for mm_output_0, mm_output_1 in zip(mm_outputs_0, mm_outputs_1):
            self.assertTrue(
                torch.allclose(
                    mm_output_0.to(torch.float32), mm_output_1.to(torch.float32)
                )
            )
            self.assertEqual(mm_output_0.stride(), mm_output_1.stride())
            self.assertEqual(mm_output_0.dtype, mm_output_1.dtype)