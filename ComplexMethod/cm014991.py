def test_powsum_dtype_kwarg_1d_reduction(self, device):
        # Test dtype kwarg on CPU with bfloat16 input and float32 computation
        # Tests both the 1D reduction path (explicit conversion) and larger reductions (kernel handles it)
        ords = [0.5, 1, 2, 3]

        # Test case where reduction dims have size > 1 (kernel handles dtype conversion)
        for input_size in [(10,), (4, 5), (3, 4, 5)]:
            for ord in ords:
                x = make_tensor(input_size, dtype=torch.bfloat16, device=device, low=0.1, high=0.9)
                for dim in [None, 0, -1]:
                    if dim == -1 and len(input_size) <= 1:
                        continue
                    for keepdim in [True, False]:
                        result = torch.linalg._powsum(x, ord, dim=dim, keepdim=keepdim, dtype=torch.float32)
                        expected = x.to(torch.float32).abs().pow(ord).sum(dim=dim, keepdim=keepdim)
                        self.assertEqual(result.dtype, torch.float32)
                        self.assertEqual(result, expected)

        # Test case where reduction dims have size 1 (explicit conversion path)
        x = make_tensor((1, 5), dtype=torch.bfloat16, device=device, low=0.1, high=0.9)
        for ord in ords:
            result = torch.linalg._powsum(x, ord, dim=0, keepdim=True, dtype=torch.float32)
            expected = x.to(torch.float32).abs().pow(ord).sum(dim=0, keepdim=True)
            self.assertEqual(result.dtype, torch.float32)
            self.assertEqual(result, expected)