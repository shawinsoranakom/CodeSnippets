def test_comparison_ops_with_type_promotion(self, device):
        value_for_type = {
            torch.uint8: (1 << 5),
            torch.int8: (1 << 5),
            torch.int16: (1 << 10),
            torch.int32: (1 << 20),
            torch.int64: (1 << 35),
            torch.float16: (1 << 10),
            torch.float32: (1 << 20),
            torch.float64: (1 << 35),
            torch.complex64: (1 << 20),
            torch.complex128: (1 << 35)
        }
        comparison_ops = [
            dict(
                name="lt",
                out_op=lambda x, y, d: torch.lt(x, y, out=torch.empty(0, dtype=torch.bool, device=d)),
                ret_op=lambda x, y: torch.lt(x, y),
                compare_op=operator.lt,
            ),
            dict(
                name="le",
                out_op=lambda x, y, d: torch.le(x, y, out=torch.empty(0, dtype=torch.bool, device=d)),
                ret_op=lambda x, y: torch.le(x, y),
                compare_op=operator.le,
            ),
            dict(
                name="gt",
                out_op=lambda x, y, d: torch.gt(x, y, out=torch.empty(0, dtype=torch.bool, device=d)),
                ret_op=lambda x, y: torch.gt(x, y),
                compare_op=operator.gt,
            ),
            dict(
                name="ge",
                out_op=lambda x, y, d: torch.ge(x, y, out=torch.empty(0, dtype=torch.bool, device=d)),
                ret_op=lambda x, y: torch.ge(x, y),
                compare_op=operator.ge,
            ),
            dict(
                name="eq",
                out_op=lambda x, y, d: torch.eq(x, y, out=torch.empty(0, dtype=torch.bool, device=d)),
                ret_op=lambda x, y: torch.eq(x, y),
                compare_op=operator.eq,
            ),
            dict(
                name="ne",
                out_op=lambda x, y, d: torch.ne(x, y, out=torch.empty(0, dtype=torch.bool, device=d)),
                ret_op=lambda x, y: torch.ne(x, y),
                compare_op=operator.ne,
            ),
        ]
        for op in comparison_ops:
            for dt1 in get_all_math_dtypes(device):
                for dt2 in get_all_math_dtypes(device):
                    if (dt1.is_complex or dt2.is_complex) and not (op["name"] == "eq" or op["name"] == "ne"):
                        continue
                    val1 = value_for_type[dt1]
                    val2 = value_for_type[dt2]
                    t1 = torch.tensor([val1], dtype=dt1, device=device)
                    t2 = torch.tensor([val2], dtype=dt2, device=device)
                    expected = torch.tensor([op["compare_op"](val1, val2)], dtype=torch.bool)

                    out_res = op["out_op"](t1, t2, device)
                    self.assertEqual(out_res, expected)
                    self.assertTrue(out_res.dtype == torch.bool)
                    self.assertTrue(t1.dtype == dt1)
                    self.assertTrue(t2.dtype == dt2)

                    out_res = op["ret_op"](t1, t2)
                    self.assertEqual(out_res, expected)
                    self.assertTrue(out_res.dtype == torch.bool)
                    self.assertTrue(t1.dtype == dt1)
                    self.assertTrue(t2.dtype == dt2)

                    # test that comparing a zero dim tensor with another zero dim tensor has type promotion behavior
                    t1 = torch.tensor(val1, dtype=dt1, device=device)
                    t2 = torch.tensor(val2, dtype=dt2, device=device)
                    expected = torch.tensor(op["compare_op"](val1, val2), dtype=torch.bool)

                    out_res = op["out_op"](t1, t2, device)
                    self.assertEqual(out_res, expected)
                    self.assertTrue(out_res.dtype == torch.bool)
                    self.assertTrue(t1.dtype == dt1)
                    self.assertTrue(t2.dtype == dt2)

                    out_res = op["ret_op"](t1, t2)
                    self.assertEqual(out_res, expected)
                    self.assertTrue(out_res.dtype == torch.bool)
                    self.assertTrue(t1.dtype == dt1)
                    self.assertTrue(t2.dtype == dt2)