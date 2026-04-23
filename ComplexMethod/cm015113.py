def test_bfloat16(self, device):
        # with scalar
        bf = torch.tensor(5.5, dtype=torch.bfloat16, device=device)
        for scalar in (2.2, 5, 100000):   # bf + 100000 is inf
            self.assertEqual((bf + scalar).dtype, torch.bfloat16)
            self.assertEqual(scalar + bf, bf + scalar)

        for scalar in (complex(1, 1), complex(-2, 0), complex(0, -3)):
            self.assertEqual((bf + scalar).dtype, torch.cfloat)
            self.assertEqual(bf + scalar, scalar + bf)

        # with tensor
        for dtype in all_types_and_complex_and(torch.half, torch.bfloat16, torch.bool):
            t = torch.tensor(1, dtype=dtype, device=device)
            self.assertEqual(bf + t, t + bf)
            if dtype in (torch.float16, torch.float32, torch.float64, torch.cfloat, torch.cdouble):
                # Handles bfloat16 x float16 -> float32 promotion
                expected_dtype = dtype if dtype != torch.half else torch.float32
            elif dtype is torch.chalf:
                expected_dtype = torch.cfloat
            elif dtype in (torch.bool, torch.uint8,
                           torch.int8, torch.int16, torch.int32, torch.int64, torch.bfloat16):
                expected_dtype = torch.bfloat16
            else:
                raise AssertionError(f'Missing dtype {dtype} not tested.')

            self.assertEqual(torch.promote_types(dtype, torch.bfloat16), expected_dtype)
            self.assertEqual(torch.promote_types(torch.bfloat16, dtype), expected_dtype)
            self.assertEqual((bf + t).dtype, expected_dtype)