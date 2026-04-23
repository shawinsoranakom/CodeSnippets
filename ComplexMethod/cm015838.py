def test_benchmark_real_trace_symbolic(self):
        """Verify benchmarking uses real values but tracing uses symbolic shapes."""
        if self.device != "cuda":
            self.skipTest("Test requires CUDA")

        # Track shapes seen by the real op implementation
        shapes_seen = []

        test_op_name = f"test_lib::shape_tracker_{id(self)}"

        def decomposition(x, weight):
            return x @ weight

        @torch.library.custom_op(test_op_name, mutates_args=())
        def shape_tracker_op(x: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
            # This runs during benchmarking with REAL values
            shapes_seen.append(x.shape[0])
            return x @ weight

        @shape_tracker_op.register_fake
        def _(x, weight):
            return torch.empty(
                x.shape[0], weight.shape[1], device=x.device, dtype=x.dtype
            )

        register_custom_op_autotuning(
            shape_tracker_op,
            configs=[CustomOpConfig(decomposition)],
            name="shape_tracker_autotuned",
            input_gen_fns={
                "x": lambda t: torch.randn_like(t, device=self.device),
                "weight": lambda t: torch.randn_like(t, device=self.device),
            },
            dispatch_on={"tensor_name": "x", "dim": 0},
            split_points=[128, 512],
        )

        test_x = torch.randn(1024, 64, device=self.device, dtype=self.dtype)
        test_weight = torch.randn(64, 32, device=self.device, dtype=self.dtype)

        @torch.compile(dynamic=True)
        def test_model(x, weight):
            return shape_tracker_op(x, weight)

        torch._dynamo.mark_dynamic(test_x, 0)
        torch._dynamo.reset()
        shapes_seen.clear()

        with config.patch(max_autotune=True, fx_graph_cache=False):
            result, code = torch._inductor.utils.run_and_get_code(
                test_model, test_x, test_weight
            )

        # Verify we got concrete integers during benchmarking (not symbolic)
        unique_shapes = sorted(set(shapes_seen))
        for shape in unique_shapes:
            self.assertIsInstance(shape, int, f"Expected int, got {type(shape)}")

        # Verify we hit all 3 ranges during autotuning
        ranges_hit = set()
        for shape in shapes_seen:
            if 1 <= shape <= 128:
                ranges_hit.add("range_1_128")
            elif 129 <= shape <= 512:
                ranges_hit.add("range_129_512")
            elif shape > 512:
                ranges_hit.add("range_513_inf")

        self.assertEqual(
            len(ranges_hit),
            3,
            f"Expected 3 ranges hit during benchmarking, got {ranges_hit}",
        )

        # Verify tracing uses SYMBOLIC shapes in generated code
        import re

        has_symbolic = any(re.search(r"\bs\d+\b", c) for c in code)
        self.assertTrue(has_symbolic, "Expected symbolic shapes in generated code")