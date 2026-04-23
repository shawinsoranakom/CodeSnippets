def test_remote_cache_load_function(
        self, device, dtype, dynamic, bundle_triton, use_static_triton_launcher
    ):
        from unittest.mock import patch

        if device == GPU_TYPE and not HAS_GPU:
            raise unittest.SkipTest(f"requires {GPU_TYPE}")
        if (
            device == "cuda"
            and torch.version.hip is None
            and dtype == torch.bfloat16
            and not SM80OrLater
        ):
            raise unittest.SkipTest("requires SM80 or later")
        if use_static_triton_launcher and not (
            device in STATIC_LAUNCHER_DEVICES and bundle_triton
        ):
            raise unittest.SkipTest(
                "Static cuda launcher requires cuda and triton bundling"
            )

        def fn(x, y):
            return (x * 2, y @ y)

        a = torch.rand(25, dtype=dtype, device=device)
        b = torch.rand(5, 5, dtype=dtype, device=device)

        with (
            config.patch(
                {
                    "fx_graph_remote_cache": True,
                    "bundle_triton_into_fx_graph_cache": bundle_triton,
                    "use_static_triton_launcher": use_static_triton_launcher,
                }
            ),
            patch.dict(os.environ),
            PatchCaches(),
        ):
            os.environ.pop("TRITON_CACHE_MANAGER", None)
            for _ in range(4):
                with fresh_cache():
                    compiled_fn = torch.compile(fn, dynamic=dynamic)
                    self.assertEqual(fn(a, b), compiled_fn(a, b))
                reset()

            self.assertEqual(global_stats.fx_graph, Stats(1, 3, 1))

            with torch.compiler.config.patch({"cache_key_tag": "test"}), fresh_cache():
                compiled_fn = torch.compile(fn, dynamic=dynamic)
                self.assertEqual(fn(a, b), compiled_fn(a, b))

            self.assertEqual(global_stats.fx_graph, Stats(2, 3, 2))

        # Check that the cache entries seem reasonable
        for k in global_stats.fx_graph.cache:
            self.assertRegex(k, r"pt2:fx-graph-v1::[0-9a-z]{52}:c[0-9]+")