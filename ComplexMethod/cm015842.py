def test_rms_norm_bwd(
        self,
        wdtype,
        split_reductions,
        shape,
        max_autotune,
        initial_xblock,
        add_1dim,
    ):
        # max_autotune can be slow and cost resource, trim down the tests
        # for max autotune
        if max_autotune and not (
            wdtype == torch.bfloat16
            and not split_reductions
            and shape in ((32768, 768), (32769, 768))
            and initial_xblock == 1
            and inductor_config.triton.mix_order_reduction
        ):
            self.skipTest("Skip non-critical tests to save resources.")

        if shape != (1000000, 256) and add_1dim:
            self.skipTest("Skip non-critical tests to save resources.")

        def f(x, w, eps):
            orig_dtype = x.dtype

            x = x.float()
            rsqrt = torch.rsqrt((x * x).sum(dim=-1) / x.shape[-1] + eps)
            y = (x * rsqrt[:, None] * w).to(dtype=orig_dtype)
            return y

        def fwd_bwd(f):
            x.grad = None
            w.grad = None
            out = f(x, w, eps)
            out.backward(dy)
            return x.grad, w.grad

        torch.manual_seed(1337)

        # M, N = 1152 * 500, 384
        M, N = shape
        x = torch.randn(M, N, dtype=torch.bfloat16, device=GPU_TYPE, requires_grad=True)
        if add_1dim:
            x = x[:, None, :]

        w = torch.randn(N, dtype=wdtype, device=GPU_TYPE, requires_grad=True)
        dy = torch.randn_like(x)
        eps = 1e-5

        opt_f = torch.compile(
            f,
            options={
                "split_reductions": split_reductions,
                "triton.mix_order_reduction_initial_xblock": initial_xblock,
                **(
                    {
                        "max_autotune": True,
                        "coordinate_descent_tuning": True,
                    }
                    if max_autotune
                    else {}
                ),
            },
        )

        ref = fwd_bwd(f)
        act, (_, bwd_wrapper) = utils.run_and_get_code(fwd_bwd, opt_f)

        self.assertTrue(same(ref, act, tol=1e-2), f"ref:\n{ref}\nact:\n{act}")
        self.assertEqual(
            inductor_config.triton.mix_order_reduction,
            metrics.codegen_mix_order_reduction,
        )