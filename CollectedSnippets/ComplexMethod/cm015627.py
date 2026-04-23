def test_autograd_inductor_guards(self, device, dtype, requires_grad):
        """
        Test caching the same graph, but under conditions that introduce guards
        for tensor sizes < int32.
        See test_codecache::TestFxGraphCache::test_cache_load_with_guards_int32_bounds.
        """
        if device == GPU_TYPE and not HAS_GPU:
            raise unittest.SkipTest(f"requires {GPU_TYPE}")
        if device == "cuda" and dtype == torch.bfloat16 and not SM80OrLater:
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
        expected_hits = expected_misses = expected_saves = 0
        expected_guard_misses = 0
        for a_shape, b_shape in shapes:
            a = torch.rand(
                a_shape, device=device, dtype=dtype, requires_grad=requires_grad
            )
            b = torch.rand(
                b_shape, device=device, dtype=dtype, requires_grad=requires_grad
            )

            # AVOID a dynamo reset here. We expect guards to have been
            # added that will be violated with the new shape. We should
            # see a recompilation (along with a cache miss).
            res1 = compiled_fn(a, b)
            # A first call should miss in the cache.
            expected_misses += 1  # noqa: SIM113
            self.assertEqual(
                counters["aot_autograd"]["autograd_cache_miss"], expected_misses
            )
            self.assertEqual(
                counters["aot_autograd"]["autograd_cache_guard_miss"],
                expected_guard_misses,
            )

            self.assertEqual(
                counters["aot_autograd"]["autograd_cache_hit"], expected_hits
            )
            # Because dynamic shapes are enabled, we expect backwards to be compiled ahead of time
            # So we should see a cache save here
            expected_saves += 1  # noqa: SIM113
            self.assertEqual(
                counters["aot_autograd"]["autograd_cache_saved"], expected_saves
            )
            if requires_grad:
                res1[0].sum().backward()
                # No extra saves
                self.assertEqual(
                    counters["aot_autograd"]["autograd_cache_saved"], expected_saves
                )

            a2 = a.detach().clone().requires_grad_(requires_grad)
            b2 = b.detach().clone().requires_grad_(requires_grad)
            # A second call should hit. (First reset so in-memory guards
            # don't prevent compilation).

            # Now clear dynamo and we should see a cache hit
            # This should populate guards to dynamo's cache, so that a subsequent run with a different
            # shape will still trigger a second call to autograd_cache.
            self._clear_dynamo_and_codecache()
            res2 = compiled_fn(a2, b2)
            expected_hits += 1  # noqa: SIM113
            self.assertEqual(
                counters["aot_autograd"]["autograd_cache_miss"], expected_misses
            )
            self.assertEqual(
                counters["aot_autograd"]["autograd_cache_guard_miss"],
                expected_guard_misses,
            )
            # First compile is a regular cache miss, subsequent are guard misses
            expected_guard_misses += 1  # noqa: SIM113
            self.assertEqual(
                counters["aot_autograd"]["autograd_cache_hit"], expected_hits
            )
            self.assertEqual(
                counters["aot_autograd"]["autograd_cache_saved"], expected_saves
            )
            self.assertEqual(res1, res2)
            if requires_grad:
                res2[0].sum().backward()
                self.assertEqual(a.grad, a2.grad)