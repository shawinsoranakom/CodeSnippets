def test_layer_norm_sharing_weights(self, split_reductions, dtype, has_bias):
        if not inductor_config.triton.mix_order_reduction:
            self.skipTest("Mix order reduction not enabled")

        def f(xs, w, bias, eps):
            ys = []
            for x in xs:
                ys.append(F.layer_norm(x, x.shape[-1:], w, bias=bias, eps=eps))
            return ys

        num_norm = 3
        M, N = 32768, 768
        xs = [
            torch.randn(M, N, dtype=dtype, device=GPU_TYPE, requires_grad=True)
            for _ in range(num_norm)
        ]
        w = torch.randn(N, dtype=dtype, device=GPU_TYPE, requires_grad=True)
        b = (
            torch.randn(N, dtype=dtype, device=GPU_TYPE, requires_grad=True)
            if has_bias
            else None
        )
        dys = [torch.randn_like(xs[0]) for _ in range(num_norm)]
        eps = 1e-5

        ref = f(xs, w, b, eps)
        act = torch.compile(
            f,
            options={
                "split_reductions": split_reductions,
            },
        )(xs, w, b, eps)

        inputs_for_grad = [*xs, w]
        if has_bias:
            inputs_for_grad.append(b)
        ref_grads = torch.autograd.grad(ref, inputs_for_grad, dys)
        act_grads, (wrapper,) = utils.run_and_get_code(
            lambda: torch.autograd.grad(act, inputs_for_grad, dys)
        )
        tol = 1e-3 if dtype == torch.float32 else 1e-2
        if GPU_TYPE == "xpu":
            tol = 1e-3 if dtype == torch.float32 else 2e-2
        self.assertTrue(same((ref, ref_grads[:-2]), (act, act_grads[:-2]), tol=tol))
        if dtype == torch.float32:
            # bfloat16 cause big numerical instability for grad_weight
            # and grad_bias
            torch.testing.assert_close(
                ref_grads[-2:], act_grads[-2:], atol=tol, rtol=tol
            )
        self.assertEqual(
            metrics.codegen_mix_order_reduction,
            num_norm,
        )

        # a single mix order reduction kernel get shared
        FileCheck().check_count("MixOrderReductionGrid", 1, exactly=True).run(wrapper)