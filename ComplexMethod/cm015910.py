def test_freezing(self, device, inlinable):
        if device == GPU_TYPE and not HAS_GPU:
            raise unittest.SkipTest(f"requires {GPU_TYPE}")

        # For machines with mkldnn_fp16 support, weight_pack in mkldnn_fusion.py causes
        # the creation of a mkldnn format tensor which the current implementation does
        # not support.
        if (
            device == "cpu"
            and torch.backends.mkldnn.is_available()
            and torch.ops.mkldnn._is_mkldnn_fp16_supported()
        ):
            raise unittest.SkipTest("mkldnn tensors unsupported")

        # The shape of the frozen constant determines if it will be inlined.
        shape = (4,) if inlinable else (8, 8)

        class MM(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.param = torch.nn.Parameter(torch.rand(shape))

            def forward(self, x):
                return x @ self.param

        dtype = torch.float16

        # Populate a cache entry.
        mod1 = MM().to(device=device, dtype=dtype)
        with torch.no_grad():
            x = torch.rand(shape).to(device=device, dtype=dtype)
            out0 = mod1(x)
            out1 = torch.compile(mod1)(x)
            self.assertEqual(out0, out1)

        self.assertEqual(counters["inductor"]["fxgraph_cache_bypass"], 0)
        self.assertEqual(counters["inductor"]["fxgraph_cache_miss"], 1)
        self.assertEqual(counters["inductor"]["fxgraph_cache_hit"], 0)

        counters.clear()
        self.reset()

        # Same nn.Module, but with different parameters. In the case that the param can
        # be inlined, we should consider the actual tensor value and we expect a cache
        # miss (because the values are different here). If the param cannot be inlined,
        # then we consider only the tensor metadata and we expect a cache hit.
        mod2 = MM().to(device=device, dtype=dtype)
        self.assertNotEqual(mod1.param, mod2.param)

        with torch.no_grad():
            x = torch.rand(shape).to(device=device, dtype=dtype)
            out0 = mod2(x)
            out1 = torch.compile(mod2)(x)
            self.assertEqual(out0, out1)

        self.assertEqual(counters["inductor"]["fxgraph_cache_bypass"], 0)
        self.assertEqual(
            counters["inductor"]["fxgraph_cache_miss"], 1 if inlinable else 0
        )
        self.assertEqual(
            counters["inductor"]["fxgraph_cache_hit"], 0 if inlinable else 1
        )