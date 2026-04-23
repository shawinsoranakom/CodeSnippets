def test_honor_sm_carveout_with_triton_tma(self, carveout, op: str):
        def mm_func(a, b):
            return torch.mm(a, b)

        def scaled_mm(
            a,
            b,
            scale_a,
            scale_b,
        ):
            return torch._scaled_mm(a, b, scale_a, scale_b, out_dtype=torch.bfloat16)

        # Create large matrices to ensure we use all possible sms
        size = 2560
        a = torch.randn(size, size, device=GPU_TYPE, dtype=torch.bfloat16)
        b = (
            torch.randn(size, size, device=GPU_TYPE, dtype=torch.bfloat16)
            .transpose(0, 1)
            .contiguous()
            .transpose(0, 1)
        )
        scale_a = torch.tensor(1, dtype=torch.float32, device=GPU_TYPE)
        scale_b = torch.tensor(1, dtype=torch.float32, device=GPU_TYPE)

        args = (
            (a.to(torch.float8_e4m3fn), b.to(torch.float8_e4m3fn), scale_a, scale_b)
            if op == "scaled_mm"
            else (a, b)
        )
        func = scaled_mm if op == "scaled_mm" else mm_func

        # Set the specified carveout value
        torch._C._set_sm_carveout_experimental(carveout)
        if carveout is None:
            self.assertIsNone(torch._C._get_sm_carveout_experimental())
        else:
            self.assertEqual(torch._C._get_sm_carveout_experimental(), carveout)

        with config.patch(
            {
                "max_autotune": True,
                "triton.enable_persistent_tma_matmul": True,
                "triton.native_matmul": False,
                "max_autotune_gemm_backends": "TRITON",
                "test_configs.autotune_choice_name_regex": "tma",
            }
        ):
            compiled_mm = torch.compile(func, mode="max-autotune-no-cudagraphs")
            compiled_mm(*args)  # Warm-up compilation

            with tempfile.NamedTemporaryFile() as f:
                with torch.profiler.profile(
                    activities=[torch.profiler.ProfilerActivity.CUDA]
                ) as prof:
                    # Run with the specified carveout
                    compiled_mm(*args)

                # Export trace and analyze results
                prof.export_chrome_trace(f.name)

                # Extract grid sizes from the trace events for TMA kernels
                kernel_name = "triton_tem_fused"
                with open(f.name) as file:
                    kernel_events = [
                        {
                            "grid": evt.get("args", {}).get("grid", []),
                            "grid_size": math.prod(evt.get("args", {}).get("grid", [])),
                        }
                        for evt in json.load(file)["traceEvents"]
                        if evt.get("cat", "") == "kernel"
                        and kernel_name in evt.get("name", "").lower()
                    ]

                # We should have exactly 1 kernel event for this run
                self.assertEqual(
                    len(kernel_events),
                    1,
                    f"Expected exactly 1 kernel event, but got {len(kernel_events)}",
                )

                # Check that grid size matches expected values based on carveout
                expected_grid_size = None
                max_grid_size = torch.cuda.get_device_properties(
                    "cuda"
                ).multi_processor_count
                careveout = 0 if carveout is None else carveout
                expected_grid_size = max_grid_size - careveout

                self.assertEqual(
                    kernel_events[0]["grid_size"],
                    expected_grid_size,
                    f"Grid size {kernel_events[0]['grid_size']} doesn't match {expected_grid_size} for carveout={carveout}",
                )