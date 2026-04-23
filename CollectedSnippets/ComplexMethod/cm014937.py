def _test_reduce_integer_upcast(self, fn, has_out=True, test_complex=True):
        shape = (3, 4, 5)
        reduced_shape = fn(torch.ones(shape)).shape

        def _test_out(dtype, other_dtype):
            out = torch.ones(reduced_shape, dtype=dtype)
            result = fn(x, out=out)
            self.assertIs(out.dtype, result.dtype)
            self.assertEqual(fn(x.to(dtype)), result, exact_dtype=False)
            result = fn(x, out=out, dtype=dtype)
            self.assertIs(out.dtype, result.dtype)
            self.assertEqual(fn(x.to(dtype)), result, exact_dtype=False)
            # 'out' is favored over dtype, check error
            self.assertRaises(RuntimeError, lambda: fn(x, out=out, dtype=other_dtype))

        for dtype in [dtype for dtype in get_all_math_dtypes('cpu') if dtype != torch.float16]:
            x = torch.ones(shape, dtype=dtype)
            expected_dtype = dtype if dtype.is_floating_point or dtype.is_complex else torch.int64
            self.assertIs(expected_dtype, fn(x).dtype)
            self.assertEqual(fn(x.to(expected_dtype)), fn(x))

            if dtype.is_floating_point:
                other_dtype = torch.float32 if dtype == torch.float64 else torch.float64
            elif dtype.is_complex:
                other_dtype = torch.complex64 if dtype == torch.complex128 else torch.complex128
            else:
                other_dtype = torch.int32 if dtype != torch.int32 else torch.int16
            self.assertIs(other_dtype, fn(x, dtype=other_dtype).dtype)
            self.assertEqual(fn(x.to(other_dtype)), fn(x, dtype=other_dtype), exact_dtype=False)

            # test mixed int/float/complex
            if dtype.is_floating_point:
                mixed_dtypes = [torch.int32, torch.complex64]
            elif dtype.is_complex:
                mixed_dtypes = [torch.int32, torch.float32]
            else:
                mixed_dtypes = [torch.float32, torch.complex64]

            for mixed_dtype in mixed_dtypes:
                self.assertIs(mixed_dtype, fn(x, dtype=mixed_dtype).dtype)
                self.assertEqual(fn(x.to(mixed_dtype)), fn(x, dtype=mixed_dtype), exact_dtype=False)

                if has_out:
                    _test_out(dtype, other_dtype)
                    _test_out(dtype, mixed_dtype)