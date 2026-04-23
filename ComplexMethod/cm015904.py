def test_cache_load_function(
        self, device, dtype, dynamic, bundle_triton, use_static_triton_launcher, grad
    ):
        """
        Verify that we can populate and load functions from the cache.
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
        if use_static_triton_launcher and not (
            device in STATIC_LAUNCHER_DEVICES and bundle_triton
        ):
            raise unittest.SkipTest(
                "Static triton launcher requires cuda/xpu and triton bundling"
            )
        if use_static_triton_launcher and TEST_WITH_ROCM:
            raise unittest.SkipTest("Static cuda launcher doesn't work with ROCM")

        grad_multiplier = 2 if grad else 1

        def fn(x, y):
            yy = y @ y
            return x * 2 + yy.view(25)

        a_orig = torch.rand(25, dtype=dtype, device=device)
        b_orig = torch.rand(5, 5, dtype=dtype, device=device)

        with config.patch(
            bundle_triton_into_fx_graph_cache=bundle_triton,
            use_static_triton_launcher=use_static_triton_launcher,
        ):
            compiled_fn = torch.compile(fn, dynamic=dynamic)

            a1 = a_orig.clone().requires_grad_(grad)
            b1 = b_orig.clone().requires_grad_(grad)
            a2 = a_orig.clone().requires_grad_(grad)
            b2 = b_orig.clone().requires_grad_(grad)

            # A first call should miss in the cache.
            eager_result = fn(a1, b1)
            compiled_result = compiled_fn(a2, b2)
            self.assertEqual(eager_result, compiled_result)
            if grad:
                eager_result.sum().backward()
                compiled_result.sum().backward()
                self.assertEqual(a1.grad, a2.grad)
                self.assertEqual(b1.grad, b2.grad)
            self.assertEqual(
                counters["inductor"]["fxgraph_cache_miss"], grad_multiplier * 1
            )
            self.assertEqual(counters["inductor"]["fxgraph_cache_hit"], 0)
            self.assertEqual(counters["inductor"]["fxgraph_lookup_write_file"], 0)

            # we expect:
            #  .ttir
            #  .ttgir
            #  .llir
            #  .ptx (cuda) or .spv (xpu)
            #  .json
            #  __grp__.*.json
            # optionally, we can also get
            #  .cubin (CUDA only)
            #  .source (new versions of triton only, triton-lang/triton#6992)

            # to avoid depending on the device and triton version, just assert that
            # we have at least 6 kernels.
            save_and_read_min_artifact_count = 6
            if bundle_triton and device != "cpu":
                self.assertGreaterEqual(
                    counters["inductor"]["triton_bundler_save_kernel"],
                    grad_multiplier * save_and_read_min_artifact_count,
                )
                self.assertEqual(
                    counters["inductor"]["triton_bundler_read_and_emit_kernel"], 0
                )
                if use_static_triton_launcher:
                    self.assertEqual(
                        counters["inductor"]["triton_bundler_save_static_autotuner"],
                        grad_multiplier if device in STATIC_LAUNCHER_DEVICES else 0,
                    )
                    self.assertEqual(
                        counters["inductor"]["triton_bundler_load_static_autotuner"], 0
                    )

            # A second call should hit. (First reset so in-memory guards
            # don't prevent compilation).
            self.reset()

            # Clean triton kernels
            shutil.rmtree(os.path.join(cache_dir(), "triton"), ignore_errors=True)

            a1 = a_orig.clone().requires_grad_(grad)
            b1 = b_orig.clone().requires_grad_(grad)
            a2 = a_orig.clone().requires_grad_(grad)
            b2 = b_orig.clone().requires_grad_(grad)

            eager_result = fn(a1, b1)
            compiled_result = compiled_fn(a2, b2)
            self.assertEqual(eager_result, compiled_result)
            if grad:
                eager_result.sum().backward()
                compiled_result.sum().backward()
                self.assertEqual(a1.grad, a2.grad)
                self.assertEqual(b1.grad, b2.grad)
            self.assertEqual(
                counters["inductor"]["fxgraph_cache_miss"], grad_multiplier * 1
            )
            self.assertEqual(
                counters["inductor"]["fxgraph_cache_hit"], grad_multiplier * 1
            )
            self.assertEqual(
                counters["inductor"]["fxgraph_lookup_write_file"], grad_multiplier * 1
            )

            if bundle_triton and device != "cpu":
                self.assertGreaterEqual(
                    counters["inductor"]["triton_bundler_save_kernel"],
                    grad_multiplier * save_and_read_min_artifact_count,
                )
                self.assertGreaterEqual(
                    counters["inductor"]["triton_bundler_read_and_emit_kernel"],
                    grad_multiplier * save_and_read_min_artifact_count,
                )
                if use_static_triton_launcher:
                    self.assertEqual(
                        counters["inductor"]["triton_bundler_save_static_autotuner"],
                        grad_multiplier if device in STATIC_LAUNCHER_DEVICES else 0,
                    )
                    self.assertEqual(
                        counters["inductor"]["triton_bundler_load_static_autotuner"],
                        grad_multiplier if device in STATIC_LAUNCHER_DEVICES else 0,
                    )

            self.reset()

            a1 = a_orig.clone().requires_grad_(grad)
            b1 = b_orig.clone().requires_grad_(grad)
            a2 = a_orig.clone().requires_grad_(grad)
            b2 = b_orig.clone().requires_grad_(grad)

            eager_result = fn(a1, b1)
            if grad:
                eager_result.sum().backward()
            with torch.compiler.config.patch({"cache_key_tag": "test"}):
                compiled_result = compiled_fn(a2, b2)
                if grad:
                    compiled_result.sum().backward()
            self.assertEqual(eager_result, compiled_result)
            if grad:
                self.assertEqual(a1.grad, a2.grad)
                self.assertEqual(b1.grad, b2.grad)

            self.assertEqual(
                counters["inductor"]["fxgraph_cache_miss"], grad_multiplier * 2
            )
            self.assertEqual(
                counters["inductor"]["fxgraph_cache_hit"], grad_multiplier * 1
            )
            self.assertEqual(
                counters["inductor"]["fxgraph_lookup_write_file"], grad_multiplier * 1
            )

            if bundle_triton and device != "cpu":
                self.assertGreaterEqual(
                    counters["inductor"]["triton_bundler_save_kernel"],
                    grad_multiplier * save_and_read_min_artifact_count * 2,
                )
                self.assertGreaterEqual(
                    counters["inductor"]["triton_bundler_read_and_emit_kernel"],
                    grad_multiplier * save_and_read_min_artifact_count,
                )
                if use_static_triton_launcher:
                    self.assertEqual(
                        counters["inductor"]["triton_bundler_save_static_autotuner"],
                        grad_multiplier * 2 if device in STATIC_LAUNCHER_DEVICES else 0,
                    )
                    self.assertEqual(
                        counters["inductor"]["triton_bundler_load_static_autotuner"],
                        grad_multiplier if device in STATIC_LAUNCHER_DEVICES else 0,
                    )