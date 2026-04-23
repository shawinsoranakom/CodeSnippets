def test_grad_scaling_unscale(self, device, dtype):
        device = torch.device(device)
        device0 = "cuda:0" if device.type == "cuda" else "cpu"
        inv_scale = torch.full((1,), 0.25, dtype=torch.float, device=device0)
        found_inf = torch.full((1,), 0.0, dtype=torch.float, device=device0)

        size = 20
        g = torch.full((size, size), 4.0, dtype=dtype, device=device0)
        ginf = g.clone()
        ginf[2, 2] = float('inf')
        gnan = g.clone()
        gnan[2, 2] = float('nan')

        # Tries selected combinations of
        #  - contiguous grads
        #  - g.clone().t() which is not contiguous but still non overlapping and dense
        #  - variants of g.clone()[:, :5] which are not non overlapping and dense
        # Non overlapping and dense grads route into a multi tensor apply kernel,
        # others use a fallback per-tensor kernel, so we should try both.
        cases = (
            ([g.clone(), g.clone()], False),
            ([g.clone(), g.clone().t()], False),
            ([g.clone(), g.clone()[:, :5]], False),
            ([g.clone()[:, :5], g.clone()[:, :5]], False),
            ([g.clone(), ginf.clone()], True),
            ([g.clone(), gnan.clone()], True),
            ([g.clone(), ginf.clone()[:, :5]], True),
            ([g.clone(), gnan.clone()[:, :5]], True),
            ([ginf.clone(), g.clone()[:, :5]], True),
            ([ginf.clone()[:, :5], g.clone()[:, :5]], True),
        )

        for grads, has_inf in cases:
            found_inf.zero_()
            torch._amp_foreach_non_finite_check_and_unscale_(grads, found_inf, inv_scale)
            if has_inf:
                self.assertEqual(found_inf, 1.0)
            else:
                self.assertEqual(found_inf, 0.0)
                for grad in grads:
                    self.assertEqual(grad, torch.ones_like(grad), rtol=1e-5, atol=1e-7)

        # When passing lists with mismatched dtypes to a raw
        # _amp_foreach_non_finite_check_and_unscale_ call on CUDA,
        # it's expected to fall back to single-tensor TensorIterator kernel.
        grads = [g.clone(), g.to(dtype=torch.float16)]
        torch._amp_foreach_non_finite_check_and_unscale_(grads, found_inf, inv_scale)
        for grad in grads:
            self.assertEqual(grad, torch.ones_like(grad), rtol=1e-5, atol=1e-7)

        # Passing lists with mismatched devices to a raw
        # _amp_foreach_non_finite_check_and_unscale_ call should raise errors.
        if device.type == "cuda" and TEST_MULTIGPU:
            with self.assertRaisesRegex(RuntimeError, r"Expected all tensors to be on the same device"):
                torch._amp_foreach_non_finite_check_and_unscale_([g.clone(), g.to(device="cuda:1")],
                                                                 found_inf,
                                                                 inv_scale)

        # Creates a list of grads with mismatched dtypes and devices, to ensure
        # scaler._unscale_grads_ organizes grads by dtype and device before calling
        # _amp_foreach_non_finite_check_and_unscale_ on each set.
        # If inject_inf >= 0, writes an inf into one grad for _unscale_grads_ to find.
        def perfect_storm_grads(inject_inf):
            grads = [g.clone(), g.clone()[:, :5], g.to(dtype=torch.float16), g.to(dtype=torch.float16)]
            if device.type == "cuda" and TEST_MULTIGPU:
                grads += [g.to(device="cuda:1"),
                          g.to(device="cuda:1")[:, :5],
                          g.to(device="cuda:1", dtype=torch.float16),
                          g.to(device="cuda:1", dtype=torch.float16)]
            if inject_inf >= 0:
                grads[inject_inf][2, 2] = float('inf')
            return grads

        GradScaler = partial(torch.GradScaler, device=device.type)
        scaler = GradScaler()
        dummy_params = [torch.empty_like(g) for g in perfect_storm_grads(-1)]
        dummy_opt = torch.optim.SGD(dummy_params, lr=1.)

        # Ensures the inf/nan checking can find an inf injected onto any grad in the perfect storm.
        for inject_inf in range(-1, len(dummy_params)):
            found_inf = torch.full((1,), 0.0, dtype=torch.float, device=device0)
            grads = perfect_storm_grads(inject_inf)
            for i, p in enumerate(dummy_params):
                p.grad = grads[i]
            found_inf_per_device = scaler._unscale_grads_(dummy_opt, inv_scale, found_inf, True)
            if inject_inf < 0:
                # No inf was injected, ensures unscaling worked normally.
                self.assertTrue(sum(v.item() for v in found_inf_per_device.values()) == 0)
                for grad in grads:
                    self.assertEqual(grad, torch.ones_like(grad), rtol=1e-5, atol=1e-7)
            else:
                # inf was injected, ensures inf was found.
                self.assertTrue(sum(v.item() for v in found_inf_per_device.values()) == 1)