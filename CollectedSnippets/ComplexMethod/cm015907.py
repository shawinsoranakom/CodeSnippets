def test_cache_hot_load_caching_precompile(self, device, dtype, dynamic):
        """
        Verify that we can populate and hot load functions from the cache.
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

        def fn(x, y):
            return x.sin() @ y

        a = torch.rand(100, 100, dtype=dtype, device=device, requires_grad=True)
        b = torch.rand(100, 100, dtype=dtype, device=device, requires_grad=True)

        # Record artifacts
        with fresh_cache():
            compiled_fn = torch.compile(fn, dynamic=dynamic)

            # A first call should miss in the cache.
            eager_result = fn(a, b)
            compiled_result = compiled_fn(a, b)
            compiled_result.sum().backward()
            self.assertEqual(eager_result, compiled_result)
            self.assertEqual(counters["aot_autograd"]["autograd_cache_miss"], 1)
            self.assertEqual(counters["aot_autograd"]["autograd_cache_hit"], 0)
            self.assertEqual(counters["dynamo_cache"]["dynamo_cache_miss"], 1)
            self.assertEqual(counters["dynamo_cache"]["dynamo_cache_hit"], 0)

        artifacts = torch.compiler.save_cache_artifacts()

        self.assertIsNotNone(artifacts)

        artifact_bytes, cache_info = artifacts

        autotune_expect = 2 if device == GPU_TYPE else 0
        self.assertEqual(len(cache_info.inductor_artifacts), 2)
        self.assertEqual(len(cache_info.autotune_artifacts), autotune_expect)
        self.assertEqual(len(cache_info.aot_autograd_artifacts), 1)
        self.assertEqual(len(cache_info.pgo_artifacts), 0)
        self.assertEqual(len(cache_info.precompile_artifacts), 1)

        self.reset()

        # Clean triton kernels
        shutil.rmtree(os.path.join(cache_dir(), "triton"), ignore_errors=True)

        # We did not load anything so dont hit yet
        with fresh_cache():
            eager_result = fn(a, b)
            # With caching precompile, we have to re torch.compile the function
            # to trigger cache lookup
            compiled_fn = torch.compile(fn, dynamic=dynamic)
            compiled_result = compiled_fn(a, b)
            compiled_result.sum().backward()
            self.assertEqual(eager_result, compiled_result)
            self.assertEqual(counters["aot_autograd"]["autograd_cache_miss"], 2)
            self.assertEqual(counters["aot_autograd"]["autograd_cache_hit"], 0)
            self.assertEqual(counters["dynamo_cache"]["dynamo_cache_miss"], 2)
            self.assertEqual(counters["dynamo_cache"]["dynamo_cache_hit"], 0)
        self.reset()
        # Clean triton kernels
        shutil.rmtree(os.path.join(cache_dir(), "triton"), ignore_errors=True)

        # Hot load and hit
        with fresh_cache(), torch.compiler.set_stance("fail_on_recompile"):
            cache_info = torch.compiler.load_cache_artifacts(artifact_bytes)
            self.assertEqual(len(cache_info.inductor_artifacts), 2)
            self.assertEqual(len(cache_info.autotune_artifacts), autotune_expect)
            self.assertEqual(len(cache_info.aot_autograd_artifacts), 1)
            self.assertEqual(len(cache_info.pgo_artifacts), 0)
            self.assertEqual(len(cache_info.precompile_artifacts), 1)

            # With caching precompile, we have to re torch.compile the function
            # to trigger cache lookup
            compiled_fn = torch.compile(fn, dynamic=dynamic)

            eager_result = fn(a, b)
            compiled_result = compiled_fn(a, b)
            compiled_result.sum().backward()
            self.assertEqual(eager_result, compiled_result)
            self.assertEqual(counters["aot_autograd"]["autograd_cache_miss"], 2)
            self.assertEqual(counters["aot_autograd"]["autograd_cache_hit"], 0)
            self.assertEqual(counters["dynamo_cache"]["dynamo_cache_miss"], 2)
            self.assertEqual(counters["dynamo_cache"]["dynamo_cache_hit"], 1)