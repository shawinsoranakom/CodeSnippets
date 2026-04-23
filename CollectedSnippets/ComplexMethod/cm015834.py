def test_max_autotune_cutlass_backend_bmm(
        self,
        dynamic: bool,
        use_aoti: bool = False,
        max_autotune_gemm_backends: str = "CUTLASS",
        dtype: torch.dtype = torch.float16,
        use_expand: bool = False,
    ):
        """
        Main test for bmm.
        """

        class MyModel(torch.nn.Module):
            def forward(self, a, b):
                return torch.bmm(a, b)

        model = MyModel().to(GPU_TYPE)
        # B, M, N, K
        shapes = [
            (10, 4096, 2048, 25728),
            (20, 2048, 1024, 12864),
        ]
        shapes = shapes[0:1] if not dynamic else shapes

        inputs = []
        for B, M, N, K in shapes:
            if use_expand:
                # Create A using unsqueeze and expand
                A = (
                    torch.randn(M, K)
                    .to(GPU_TYPE)
                    .to(dtype)
                    .unsqueeze(0)
                    .expand(B, -1, -1)
                )
            else:
                # Original method
                A = torch.randn(B, M, K).to(GPU_TYPE).to(dtype)

            B_tensor = torch.randn(B, N, K).to(GPU_TYPE).to(dtype).permute(0, 2, 1)
            inputs.append((A, B_tensor))
        dynamic_shapes = (
            {
                "a": {0: Dim.DYNAMIC, 1: Dim.DYNAMIC, 2: Dim.DYNAMIC},
                "b": {0: Dim.DYNAMIC, 1: Dim.DYNAMIC, 2: Dim.DYNAMIC},
            }
            if dynamic
            else None
        )
        with config.patch(
            {
                "max_autotune": True,
                "max_autotune_gemm_backends": max_autotune_gemm_backends,
                "cutlass.cutlass_max_profiling_configs": 2,
            }
        ):
            expected = [model(*input) for input in inputs]
            if use_aoti:
                actual = AOTIRunnerUtil.run_multiple(
                    model, inputs, dynamic_shapes=dynamic_shapes
                )
            else:
                compiled_model = torch.compile(model, dynamic=dynamic)
                actual = [compiled_model(*input) for input in inputs]
            torch.testing.assert_close(actual, expected)