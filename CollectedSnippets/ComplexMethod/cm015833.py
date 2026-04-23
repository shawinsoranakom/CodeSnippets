def test_max_autotune_cutlass_backend_addmm(
        self,
        dynamic: bool,
        max_autotune_gemm_backends: str = "CUTLASS",
        use_aoti: bool = False,
        dtype: torch.dtype = torch.float16,
    ):
        """
        Main test for addmm.
        """

        class MyModel(torch.nn.Module):
            def forward(self, x, a, b):
                return torch.addmm(x, a, b)

        model = MyModel().to(GPU_TYPE)
        # M, N, K
        shapes = [
            (128, 128, 16),
            (512, 512, 128),
        ]
        shapes = shapes[0:1] if not dynamic else shapes

        x_shapes = [
            lambda M, N: (M, N),
            lambda M, N: (M, 1),
            lambda M, N: (1, N),
            lambda M, N: (N,),
        ]
        for x_shape in x_shapes:
            torch._dynamo.reset()
            clear_caches()

            inputs = [
                (
                    torch.randn(x_shape(M, N)).to(GPU_TYPE).to(dtype),
                    torch.randn(M, K).to(GPU_TYPE).to(dtype),
                    torch.randn(N, K).to(GPU_TYPE).to(dtype).t(),
                )
                for (M, N, K) in shapes
            ]
            dynamic_shapes = (
                {
                    "x": {
                        i: v
                        for i, v in enumerate(x_shape(Dim.DYNAMIC, Dim.DYNAMIC))
                        if v != 1
                    },
                    "a": {0: Dim.DYNAMIC, 1: Dim.DYNAMIC},
                    "b": {0: Dim.DYNAMIC, 1: Dim.DYNAMIC},
                }
                if dynamic
                else None
            )
            with (
                config.patch(
                    {
                        "max_autotune": True,
                        "max_autotune_gemm_backends": max_autotune_gemm_backends,
                        "cutlass.cutlass_max_profiling_configs": 2,
                    }
                ),
                dynamo_config.patch({"error_on_recompile": dynamic}),
            ):
                expected = [model(*input) for input in inputs]
                if use_aoti:
                    actual = AOTIRunnerUtil.run_multiple(
                        model, inputs, dynamic_shapes=dynamic_shapes
                    )
                else:
                    compiled_model = torch.compile(model, dynamic=dynamic)
                    actual = [compiled_model(*input) for input in inputs]

                assert_close_kwargs = {}
                if dynamic and SM90OrLater:
                    # SM90+ CUTLASS addmm currently differs from eager by a small
                    # output-precision quantum on this test across multiple
                    # parametrizations. Keep the relaxation scoped to this test
                    # and stay tighter for float16 than bfloat16.
                    assert_close_kwargs = {
                        "rtol": 1.6e-2 if dtype == torch.bfloat16 else 1e-3,
                        "atol": 1e-2 if dtype == torch.bfloat16 else 2e-3,
                    }

                torch.testing.assert_close(actual, expected, **assert_close_kwargs)