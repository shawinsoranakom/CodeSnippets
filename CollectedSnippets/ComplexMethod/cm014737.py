def test_upsamplingBiMode2d(self, device, antialias, align_corners, mode, memory_format):
        # Forward AD does not support XLA because XLA tensors don't have storage
        check_forward_ad = torch.device(device).type != 'xla'

        if mode == "lanczos":
            if torch.device(device).type != "cpu":
                raise SkipTest("Lanczos mode is only supported on CPU")
            if not antialias:
                raise SkipTest("Lanczos mode requires antialias=True")
            if align_corners:
                raise SkipTest("Lanczos mode does not support align_corners=True")

        kwargs = dict(mode=mode, align_corners=align_corners, antialias=antialias)
        # test float scale factor up & downsampling
        for scale_factor in [0.5, 1.5, 2]:
            in_t = torch.ones(
                2, 3, 8, 8, device=device,
                dtype=torch.double).contiguous(memory_format=memory_format).requires_grad_()
            out_size = int(math.floor(in_t.shape[-1] * scale_factor))
            with warnings.catch_warnings(record=True) as w:
                out_t = F.interpolate(in_t, scale_factor=scale_factor, **kwargs)
            expected_out = torch.ones(2, 3, out_size, out_size, device=device, dtype=torch.double)
            self.assertEqual(expected_out, out_t)
            # Assert that memory format is carried through to the output
            self.assertTrue(out_t.is_contiguous(memory_format=memory_format))
            out_t.backward(torch.randn_like(out_t))
            self.assertTrue(in_t.grad.is_contiguous(memory_format=memory_format))

            if torch.device(device).type == 'cuda':
                # Bilinear backward is nondeterministic because of atomicAdd usage
                nondet_tol = 1e-5
            else:
                nondet_tol = 0.0

            input = torch.randn(
                2, 3, 8, 8, device=device,
                dtype=torch.double).contiguous(memory_format=memory_format).requires_grad_()
            gradcheck(
                lambda x: F.interpolate(x, out_size, **kwargs),
                [input],
                check_forward_ad=check_forward_ad, nondet_tol=nondet_tol
            )
            gradgradcheck(
                lambda x: F.interpolate(x, out_size, **kwargs),
                [input],
                check_fwd_over_rev=check_forward_ad, nondet_tol=nondet_tol
            )

            # Assert that cpu and cuda give same results
            if torch.device(device).type == 'cuda':
                for shapes in [
                    (2, 2, 3, 4), (2, 3, 4, 5), (3, 1, 2, 2), (1, 5, 3, 2)
                ]:
                    a_cuda = torch.randn(
                        *shapes, device=device, dtype=torch.double
                    ).contiguous(memory_format=memory_format).requires_grad_()
                    a_cpu = a_cuda.detach().cpu().requires_grad_()

                    with warnings.catch_warnings(record=True):
                        out_cuda = F.interpolate(a_cuda, scale_factor=scale_factor, **kwargs)
                        out_cpu = F.interpolate(a_cpu, scale_factor=scale_factor, **kwargs)

                    self.assertEqual(out_cpu, out_cuda.cpu())

                    g_cuda = torch.randn_like(out_cuda)
                    g_cpu = g_cuda.cpu()

                    out_cuda.backward(g_cuda)
                    out_cpu.backward(g_cpu)

                    self.assertEqual(a_cuda.grad, a_cpu.grad)