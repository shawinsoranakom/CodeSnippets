def test_fftn_round_trip(self, device, dtype):
        skip_helper_for_fft(device, dtype)

        norm_modes = (None, "forward", "backward", "ortho")

        # input_ndim, dim
        transform_desc = [
            *product(range(2, 5), (None, (0,), (0, -1))),
            (7, None),
            (5, (1, 3, 4)),
            (3, (1,)),
            (1, 0),
        ]

        fft_functions = [(torch.fft.fftn, torch.fft.ifftn)]

        # Real-only functions
        if not dtype.is_complex:
            # NOTE: Using ihfftn as "forward" transform to avoid needing to
            # generate true half-complex input
            fft_functions += [(torch.fft.rfftn, torch.fft.irfftn),
                              (torch.fft.ihfftn, torch.fft.hfftn)]

        for input_ndim, dim in transform_desc:
            if dtype in (torch.half, torch.complex32):
                # cuFFT supports powers of 2 for half and complex half precision
                shape = itertools.islice(itertools.cycle((2, 4, 8)), input_ndim)
            else:
                shape = itertools.islice(itertools.cycle(range(4, 9)), input_ndim)
            x = torch.randn(*shape, device=device, dtype=dtype)

            for (forward, backward), norm in product(fft_functions, norm_modes):
                if isinstance(dim, tuple):
                    s = [x.size(d) for d in dim]
                else:
                    s = x.size() if dim is None else x.size(dim)

                kwargs = {'s': s, 'dim': dim, 'norm': norm}
                y = backward(forward(x, **kwargs), **kwargs)
                # For real input, ifftn(fftn(x)) will convert to complex
                if x.dtype is torch.half and y.dtype is torch.chalf:
                    # Since type promotion currently doesn't work with complex32
                    # manually promote `x` to complex32
                    self.assertEqual(x.to(torch.chalf), y)
                else:
                    self.assertEqual(x, y, exact_dtype=(
                        forward != torch.fft.fftn or x.is_complex()))