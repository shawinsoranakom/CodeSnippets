def test_grouped_gemm_assorted_layouts(
        self,
        layout_A: str,
        layout_B: str,
    ):
        device = "cuda"
        dtype = torch.bfloat16

        G, K, N = 8, 64, 128
        M_sizes = [128] * G
        sum_M = sum(M_sizes)
        offsets = torch.tensor(
            [sum(M_sizes[: i + 1]) for i in range(G)], dtype=torch.int32, device=device
        )

        A_base = torch.randn(sum_M, K, device=device, dtype=dtype)
        A = A_base

        if layout_A == "offset":
            # allocate bigger buffer than needed, use nonzero storage offset
            storage = torch.randn(sum_M * K + 512, device=device, dtype=dtype)
            offset = 128  # skip first 128 elements
            A = torch.as_strided(storage[offset:], (sum_M, K), (K, 1))
        elif layout_A == "padded":
            # simulate row pitch > K (row_stride = K + pad)
            row_pitch = K + 8
            storage = torch.randn(sum_M * row_pitch, device=device, dtype=dtype)
            A = torch.as_strided(storage, (sum_M, K), (row_pitch, 1))
        elif layout_A == "view":
            A_storage = torch.randn(sum_M * K, device=device, dtype=dtype)
            A = A_storage.view(sum_M, K)
            if A._base is None:
                raise AssertionError
            if A.shape != (sum_M, K):
                raise AssertionError

        B = torch.randn((G, K, N), dtype=dtype, device=device) * 0.01

        if layout_B == "broadcasted":
            # Broadcast B across groups (zero stride along G)
            B = B[0].expand(G, K, N)
            if B.stride(0) != 0:
                raise AssertionError

        def grouped_gemm_fn(A_packed, B_batched, offs):
            return F.grouped_mm(A_packed, B_batched, offs=offs)

        # --- eager ---
        c_eager = grouped_gemm_fn(A, B, offsets)

        # --- compiled (CUTE backend) ---
        with config.patch(
            {
                "max_autotune": True,
                "max_autotune_gemm_backends": "CUTEDSL",
                "test_configs.autotune_choice_name_regex": "cutedsl",
                "autotune_fallback_to_aten": False,
            }
        ):
            grouped_gemm_compiled = torch.compile(
                grouped_gemm_fn, backend="inductor", dynamic=False
            )
            c_compiled = grouped_gemm_compiled(A, B, offsets)

        self.assertEqual(c_eager.dtype, dtype)
        self.assertEqual(c_compiled.dtype, dtype)
        torch.testing.assert_close(c_eager, c_compiled)