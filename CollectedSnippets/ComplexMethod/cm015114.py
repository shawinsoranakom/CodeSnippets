def test_complex_half(self, device):
        # with scalar
        chalf = torch.tensor(5.5, dtype=torch.chalf, device=device)
        for scalar in (2.2, 5, 100000):   # chalf + 100000 is inf
            self.assertEqual((chalf * scalar).dtype, torch.chalf)
            self.assertEqual(scalar * chalf, chalf * scalar)

        for scalar in (complex(1, 1), complex(-2, 0), complex(0, -3)):
            self.assertEqual((chalf * scalar).dtype, torch.chalf)
            self.assertEqual(chalf * scalar, scalar * chalf)

        # with tensor
        dtypes = all_types_and_complex_and(torch.chalf, torch.half, torch.bfloat16, torch.bool)
        for dtype in dtypes:
            t = torch.tensor(1, dtype=dtype, device=device)
            self.assertEqual(chalf * t, t * chalf)
            if dtype in (torch.float16, torch.chalf):
                expected_dtype = torch.chalf
            elif dtype in (torch.float, torch.double, torch.bfloat16):
                expected_dtype = torch.cdouble if dtype is torch.double else torch.cfloat
            elif dtype in (torch.cfloat, torch.cdouble):
                expected_dtype = dtype
            elif dtype in (torch.bool, torch.uint8,
                           torch.int8, torch.int16, torch.int32, torch.int64):
                expected_dtype = torch.chalf
            else:
                raise AssertionError(f'Missing dtype {dtype} not tested.')

            self.assertEqual(torch.promote_types(dtype, torch.chalf), expected_dtype)
            self.assertEqual(torch.promote_types(torch.chalf, dtype), expected_dtype)
            self.assertEqual((chalf * t).dtype, expected_dtype)