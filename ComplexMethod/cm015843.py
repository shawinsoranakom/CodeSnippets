def test_rms_norm_sharing_weights(self, split_reductions, dtype):
        if not inductor_config.triton.mix_order_reduction:
            self.skipTest("Mix order reduction not enabled")

        def f(xs, w, eps):
            ys = []
            for x in xs:
                ys.append(F.rms_norm(x, x.shape[-1:], w, eps=eps))
            return ys

        num_norm = 3
        M, N = 32768, 768
        xs = [
            torch.randn(M, N, dtype=dtype, device=GPU_TYPE, requires_grad=True)
            for _ in range(num_norm)
        ]
        w = torch.randn(N, dtype=dtype, device=GPU_TYPE, requires_grad=True)
        dys = [torch.randn_like(xs[0]) for _ in range(num_norm)]
        eps = 1e-5

        ref = f(xs, w, eps)

        # use float64 to compute ref_grads for precision
        # and cast back to original dtype
        xs_f64 = [x.to(torch.float64) for x in xs]
        w_f64 = w.to(torch.float64)
        dys_f64 = [dy.to(torch.float64) for dy in dys]
        ref_f64 = f(xs_f64, w_f64, eps)
        ref_grads_f64 = torch.autograd.grad(ref_f64, [*xs_f64, w_f64], dys_f64)
        ref_grads = [g.to(dtype) for g in ref_grads_f64]

        act = torch.compile(
            f,
            options={
                "split_reductions": split_reductions,
            },
        )(xs, w, eps)
        act_grads, (wrapper,) = utils.run_and_get_code(
            lambda: torch.autograd.grad(act, [*xs, w], dys)
        )
        # bfloat16 cause big numerical instability for grad_weight
        tol = 1e-3 if dtype == torch.float32 else 0.5
        self.assertTrue(same((ref, ref_grads), (act, act_grads), tol=tol))
        self.assertEqual(
            metrics.codegen_mix_order_reduction,
            num_norm,
        )

        # a single mix order reduction kernel get shared
        FileCheck().check_count("MixOrderReductionGrid", 1, exactly=True).run(wrapper)