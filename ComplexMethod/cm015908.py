def test_cache_load_with_guards_int32_bounds(self, device, dtype):
        """
        Test caching the same graph, but under conditions that introduce guards
        for tensor sizes < int32.
        """
        if device == GPU_TYPE and not HAS_GPU:
            raise unittest.SkipTest(f"requires {GPU_TYPE}")
        if (
            device == "cuda"
            and torch.version.hip is None
            and dtype == torch.bfloat16
            and not SM80OrLater
        ):
            raise unittest.SkipTest("requires CUDA SM80 or later")

        def fn(x, y):
            return (x + x, y + y)

        compiled_fn = torch.compile(fn, dynamic=True)

        # Iterate over different shapes, varying whether the total
        # size is below or above int32. For each combination, we expect
        # different guards around whether the symbolic sizes do or do
        # not exceed int32.
        shapes = (
            ((5, 6), (7, 8)),
            ((5, 6), (47000, 47001)),
            ((47000, 47001), (5, 6)),
        )
        for a_shape, b_shape in shapes:
            a = torch.rand(a_shape, device=device, dtype=dtype)
            b = torch.rand(b_shape, device=device, dtype=dtype)

            # AVOID a dynamo reset here. We expect guards to have been
            # added that will be violated with the new shape. We should
            # see a recompilation (along with a cache miss).
            counters.clear()
            res1 = compiled_fn(a, b)
            self.assertGreater(counters["inductor"]["fxgraph_cache_miss"], 0)
            self.assertEqual(counters["inductor"]["fxgraph_cache_hit"], 0)

            # A second call should hit. (Reset here to force compilation).
            counters.clear()
            self.reset()
            res2 = compiled_fn(a, b)
            self.assertEqual(counters["inductor"]["fxgraph_cache_miss"], 0)
            self.assertGreater(counters["inductor"]["fxgraph_cache_hit"], 0)

            self.assertEqual(res1, res2)