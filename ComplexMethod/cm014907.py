def test_fft_round_trip(self, device, dtype):
        skip_helper_for_fft(device, dtype)
        # Test that round trip through ifft(fft(x)) is the identity
        if dtype not in (torch.half, torch.complex32):
            test_args = list(product(
                # input
                (torch.randn(67, device=device, dtype=dtype),
                 torch.randn(80, device=device, dtype=dtype),
                 torch.randn(12, 14, device=device, dtype=dtype),
                 torch.randn(9, 6, 3, device=device, dtype=dtype)),
                # dim
                (-1, 0),
                # norm
                (None, "forward", "backward", "ortho")
            ))
        else:
            # cuFFT supports powers of 2 for half and complex half precision
            test_args = list(product(
                # input
                (torch.randn(64, device=device, dtype=dtype),
                 torch.randn(128, device=device, dtype=dtype),
                 torch.randn(4, 16, device=device, dtype=dtype),
                 torch.randn(8, 6, 2, device=device, dtype=dtype)),
                # dim
                (-1, 0),
                # norm
                (None, "forward", "backward", "ortho")
            ))

        fft_functions = [(torch.fft.fft, torch.fft.ifft)]
        # Real-only functions
        if not dtype.is_complex:
            # NOTE: Using ihfft as "forward" transform to avoid needing to
            # generate true half-complex input
            fft_functions += [(torch.fft.rfft, torch.fft.irfft),
                              (torch.fft.ihfft, torch.fft.hfft)]

        for forward, backward in fft_functions:
            for x, dim, norm in test_args:
                kwargs = {
                    'n': x.size(dim),
                    'dim': dim,
                    'norm': norm,
                }

                y = backward(forward(x, **kwargs), **kwargs)
                if x.dtype is torch.half and y.dtype is torch.complex32:
                    # Since type promotion currently doesn't work with complex32
                    # manually promote `x` to complex32
                    x = x.to(torch.complex32)
                # For real input, ifft(fft(x)) will convert to complex
                self.assertEqual(x, y, exact_dtype=(
                    forward != torch.fft.fft or x.is_complex()))