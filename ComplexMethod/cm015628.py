def test_cache_lazy_backward_for_compiled_autograd(self):
        device = "cpu"
        dtype = torch.float32
        dynamic = True
        """
        Verify that we can populate and hot load functions from the cache.
        """
        if device == GPU_TYPE and not HAS_GPU:
            raise unittest.SkipTest(f"requires {GPU_TYPE}")
        if device == "cuda" and dtype == torch.bfloat16 and not SM80OrLater:
            raise unittest.SkipTest("requires SM80 or later")

        def fn(x, y):
            return x.sin() @ y

        a = torch.rand(100, 100, dtype=dtype, device=device, requires_grad=True)
        b = torch.rand(100, 100, dtype=dtype, device=device, requires_grad=True)

        # Record artifacts
        with fresh_cache():
            compiled_fn = torch.compile(fn, dynamic=dynamic)

            # A first call should miss in the cache.
            eager_result = fn(a, b)
            expected_grads = torch.autograd.grad(eager_result.sum(), inputs=(a, b))
            compiled_result = compiled_fn(a, b)
            with torch._dynamo.compiled_autograd._enable(
                torch.compile(dynamic=dynamic)
            ):
                actual_grads = torch.autograd.grad(compiled_result.sum(), inputs=(a, b))
            if hasattr(a, "_dynamo_weak_dynamic_indices"):
                del a._dynamo_weak_dynamic_indices
            self.assertEqual(eager_result, compiled_result)
            self.assertEqual(expected_grads[0], actual_grads[0])
            self.assertEqual(expected_grads[1], actual_grads[1])
            if functorch_config.bundled_autograd_cache:
                self.assertEqual(counters["inductor"]["fxgraph_cache_miss"], 0)
                self.assertEqual(counters["inductor"]["fxgraph_cache_hit"], 0)
                self.assertEqual(counters["inductor"]["fxgraph_lookup_write_file"], 0)
            else:
                self.assertEqual(counters["inductor"]["fxgraph_cache_miss"], 3)
                self.assertEqual(counters["inductor"]["fxgraph_cache_hit"], 0)
                self.assertEqual(counters["inductor"]["fxgraph_lookup_write_file"], 0)
            self.assertEqual(counters["aot_autograd"]["autograd_cache_miss"], 1)
            self.assertEqual(counters["aot_autograd"]["autograd_cache_hit"], 0)
            self.assertEqual(counters["aot_autograd"]["autograd_cache_saved"], 1)
            self.assertEqual(counters["compiled_autograd"]["captures"], 1)

        artifacts = torch.compiler.save_cache_artifacts()

        self.assertIsNotNone(artifacts)

        artifact_bytes, cache_info = artifacts

        autotune_expect = 2 if device == GPU_TYPE else 0

        if functorch_config.bundled_autograd_cache:
            self.assertEqual(len(cache_info.inductor_artifacts), 0)
        else:
            self.assertEqual(len(cache_info.inductor_artifacts), 3)
        self.assertEqual(len(cache_info.autotune_artifacts), autotune_expect)
        self.assertEqual(len(cache_info.aot_autograd_artifacts), 1)
        self.assertEqual(len(cache_info.pgo_artifacts), 0)

        self._clear_all_caches()

        # Clean triton kernels
        shutil.rmtree(os.path.join(cache_dir(), "triton"), ignore_errors=True)

        # Hot load and hit, should not recompile
        with fresh_cache():
            cache_info = torch.compiler.load_cache_artifacts(artifact_bytes)

            if functorch_config.bundled_autograd_cache:
                self.assertEqual(len(cache_info.inductor_artifacts), 0)
            else:
                self.assertEqual(len(cache_info.inductor_artifacts), 3)
            self.assertEqual(len(cache_info.autotune_artifacts), autotune_expect)
            self.assertEqual(len(cache_info.aot_autograd_artifacts), 1)
            self.assertEqual(len(cache_info.pgo_artifacts), 0)

            for i in range(3):
                counters.clear()
                eager_result = fn(a, b)
                expected_grads = torch.autograd.grad(eager_result.sum(), inputs=(a, b))
                compiled_result = compiled_fn(a, b)
                with torch._dynamo.compiled_autograd._enable(
                    torch.compile(dynamic=dynamic)
                ):
                    actual_grads = torch.autograd.grad(
                        compiled_result.sum(), inputs=(a, b)
                    )
                if hasattr(a, "_dynamo_weak_dynamic_indices"):
                    del a._dynamo_weak_dynamic_indices
                self.assertEqual(eager_result, compiled_result)
                self.assertEqual(expected_grads[0], actual_grads[0])
                self.assertEqual(expected_grads[1], actual_grads[1])

                if i == 0:
                    # initial compile
                    if functorch_config.bundled_autograd_cache:
                        self.assertEqual(counters["inductor"]["fxgraph_cache_miss"], 0)
                        self.assertEqual(counters["inductor"]["fxgraph_cache_hit"], 0)
                    else:
                        self.assertEqual(counters["inductor"]["fxgraph_cache_miss"], 0)
                        self.assertEqual(counters["inductor"]["fxgraph_cache_hit"], 3)
                        self.assertEqual(
                            counters["inductor"]["fxgraph_lookup_write_file"], 3
                        )
                    self.assertEqual(counters["aot_autograd"]["autograd_cache_miss"], 0)
                    self.assertEqual(counters["aot_autograd"]["autograd_cache_hit"], 1)
                    self.assertEqual(
                        counters["aot_autograd"]["autograd_cache_saved"], 0
                    )
                    self.assertEqual(counters["compiled_autograd"]["captures"], 1)
                else:
                    # no recompiles
                    self.assertFalse(counters)