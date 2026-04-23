def test_fft2_numpy(self, device, dtype):
        norm_modes = REFERENCE_NORM_MODES

        # input_ndim, s
        transform_desc = [
            *product(range(2, 5), (None, (4, 10))),
        ]

        fft_functions = ['fft2', 'ifft2', 'irfft2', 'hfft2']
        if dtype.is_floating_point:
            fft_functions += ['rfft2', 'ihfft2']

        for input_ndim, s in transform_desc:
            shape = itertools.islice(itertools.cycle(range(4, 9)), input_ndim)
            input = torch.randn(*shape, device=device, dtype=dtype)
            for fname, norm in product(fft_functions, norm_modes):
                torch_fn = getattr(torch.fft, fname)
                if "hfft" in fname:
                    if not has_scipy_fft:
                        continue  # Requires scipy to compare against
                    numpy_fn = getattr(scipy.fft, fname)
                else:
                    numpy_fn = getattr(np.fft, fname)

                def fn(t: torch.Tensor, s: list[int] | None, dim: list[int] = (-2, -1), norm: str | None = None):
                    return torch_fn(t, s, dim, norm)

                torch_fns = (torch_fn, torch.jit.script(fn))

                # Once with dim defaulted
                input_np = input.cpu().numpy()
                expected = numpy_fn(input_np, s, norm=norm)
                for fn in torch_fns:
                    actual = fn(input, s, norm=norm)
                    self.assertEqual(actual, expected)

                # Once with explicit dims
                dim = (1, 0)
                expected = numpy_fn(input_np, s, dim, norm)
                for fn in torch_fns:
                    actual = fn(input, s, dim, norm)
                    self.assertEqual(actual, expected)