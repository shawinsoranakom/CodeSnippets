def test_matmul(self):
        if self.dynamic_shapes:
            self.skipTest("don't run conv with dynamic shapes")

        def fn(x, y):
            return torch.matmul(x, y)

        devices = ["cpu"]  # No cuda support for ext calls yet
        sizes = [
            [[128, 128], [128, 128]],
            [[10, 10], [10, 10]],
            [[1, 16], [16, 128]],
            [[128], [128]],
            [[128], [128, 128]],
            [[3], [3]],
            [[3, 4], [4]],
            [[10, 3, 4], [4]],
            [[10, 3, 4], [10, 4, 5]],
            [[10, 3, 4], [4, 5]],
        ]

        # Only 2D x 2D matrix multiply is supported. For non-supported sizes we
        # still want to run results verification to test that we didn't
        # accidentally fuse it, but we skip the 'is-fused' check.
        # TODO: add support for other shape combinations and make this set empty:
        skip_is_fused_check_sizes = [
            "[[128], [128]]",
            "[[128], [128, 128]]",
            "[[3], [3]]",
            "[[3, 4], [4]]",
            "[[10, 3, 4], [4]]",
            "[[10, 3, 4], [10, 4, 5]]",
            "[[10, 3, 4], [4, 5]]",
        ]
        for dtype, size, device in product(self.dtypes, sizes, devices):
            if dtype in [torch.float16, torch.bfloat16] and device == "cpu":
                continue
            try:
                size_x, size_y = size
                x = self.data_for(dtype, device, size=size_x)
                y = self.data_for(dtype, device, size=size_y)
                ref = fn(x, y)
            except Exception as e:
                # If eager mode doesn't support a dtype/op/device combo,
                # neither does the fuser.  Catch everything to avoid needing to
                # guess what errors might be thrown by eager.
                continue
            try:
                t = torch.jit.trace(fn, (x, y))
                t(x, y)
                self.assertEqual(ref, t(x, y))
                if str(size) not in skip_is_fused_check_sizes:
                    self.assertAllFused(t.graph_for(x, y))
            except Exception as e:
                raise RuntimeError(" ".join(["Failed:", str(dtype), device])) from e