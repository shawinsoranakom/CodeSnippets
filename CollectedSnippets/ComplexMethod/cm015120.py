def test_cat_out_different_dtypes(self, device):
        dtypes = all_types_and_complex_and(torch.half)
        for x_dtype, y_dtype, out_dtype in itertools.product(dtypes, dtypes, dtypes):
            out = torch.zeros(6, device=device, dtype=out_dtype)
            x = torch.tensor([1, 2, 3], device=device, dtype=x_dtype)
            y = torch.tensor([4, 5, 6], device=device, dtype=y_dtype)
            expected_out = torch.tensor([1, 2, 3, 4, 5, 6], device=device, dtype=out_dtype)
            if (((x_dtype.is_floating_point or y_dtype.is_floating_point)
                    and not (out_dtype.is_floating_point or out_dtype.is_complex))
                    or ((x_dtype.is_complex or y_dtype.is_complex) and not out_dtype.is_complex)):
                # This combinations do not support type conversion to a different class out type
                with self.assertRaises(TypeError):
                    torch.cat([x, y], out=out)
            else:
                torch.cat([x, y], out=out)
                self.assertEqual(out, expected_out, exact_dtype=True)