def test_result_type(self, device, dtypes):
        "Test result_type for tensor vs tensor and scalar vs scalar."

        def _get_dtype(x):
            "Get the dtype of x if x is a tensor. If x is a scalar, get its corresponding dtype if it were a tensor."
            if torch.is_tensor(x):
                return x.dtype
            elif isinstance(x, bool):
                return torch.bool
            elif isinstance(x, int):
                return torch.int64
            elif isinstance(x, float):
                return torch.float32
            elif isinstance(x, complex):
                return torch.complex64
            else:
                raise AssertionError(f"Unknown type {x}")

        # tensor against tensor
        a_tensor = torch.tensor((0, 1), device=device, dtype=dtypes[0])
        a_single_tensor = torch.tensor(1, device=device, dtype=dtypes[0])
        a_scalar = a_single_tensor.item()
        b_tensor = torch.tensor((1, 0), device=device, dtype=dtypes[1])
        b_single_tensor = torch.tensor(1, device=device, dtype=dtypes[1])
        b_scalar = b_single_tensor.item()
        combo = ((a_tensor, a_single_tensor, a_scalar), (b_tensor, b_single_tensor, b_scalar))
        for a, b in itertools.product(*combo):
            dtype_a = _get_dtype(a)
            dtype_b = _get_dtype(b)
            try:
                result = a + b
            except RuntimeError:
                with self.assertRaises(RuntimeError):
                    torch.promote_types(dtype_a, dtype_b)
                with self.assertRaises(RuntimeError):
                    torch.result_type(a, b)
            else:
                dtype_res = _get_dtype(result)
                if a is a_scalar and b is b_scalar and dtype_a == torch.bool and dtype_b == torch.bool:
                    # special case: in Python, True + True is an integer
                    self.assertEqual(dtype_res, torch.int64, f"a == {a}, b == {b}")
                else:
                    self.assertEqual(dtype_res, torch.result_type(a, b), f"a == {a}, b == {b}")
                if a is a_scalar and b is b_scalar:  # Python internal type determination is good enough in this case
                    continue
                if any(a is a0 and b is b0 for a0, b0 in zip(*combo)):  # a and b belong to the same class
                    self.assertEqual(dtype_res, torch.promote_types(dtype_a, dtype_b), f"a == {a}, b == {b}")