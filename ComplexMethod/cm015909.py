def test_cache_load_with_guards_static_bounds(self, device, dtype):
        """
        Test caching the same graph, but under conditions that introduce guards
        for static bounds.
        """
        if device == GPU_TYPE and not HAS_GPU:
            raise unittest.SkipTest(f"requires {GPU_TYPE}")
        if (
            device == "cuda"
            and torch.version.hip is None
            and dtype == torch.bfloat16
            and not SM80OrLater
        ):
            raise unittest.SkipTest("requires SM80 or later")

        # See lowering; for all of the pooling operators, we always guard and
        # make the height/width static.
        def fn(x):
            return torch.nn.functional.adaptive_avg_pool2d(x, [5, 7])

        compiled_fn = torch.compile(fn, dynamic=True)

        # Iterate over different input shapes. Each new shape should cause
        # a cache miss.
        shapes = ((1, 64, 8, 9), (1, 64, 9, 10), (1, 64, 10, 11))
        for shape in shapes:
            x = torch.rand(shape, device=device, dtype=dtype)

            # AVOID a dynamo reset here. For each cache hit, we expect guards
            # to have been added that will be violated with each new shape.
            # We should see a recompilation (along with a cache miss).
            counters.clear()
            res1 = compiled_fn(x)
            self.assertGreater(counters["inductor"]["fxgraph_cache_miss"], 0)
            self.assertEqual(counters["inductor"]["fxgraph_cache_hit"], 0)

            # A second call should hit.
            counters.clear()
            self.reset()
            res2 = compiled_fn(x)
            self.assertEqual(counters["inductor"]["fxgraph_cache_miss"], 0)
            self.assertGreater(counters["inductor"]["fxgraph_cache_hit"], 0)

            self.assertEqual(res1, res2)