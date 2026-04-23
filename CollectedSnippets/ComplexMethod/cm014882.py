def test_uniform_from_to(self, device, dtype):
        size = 2000
        alpha = 0.1

        float_min = torch.finfo(torch.float).min
        float_max = torch.finfo(torch.float).max
        double_min = torch.finfo(torch.double).min
        double_max = torch.finfo(torch.double).max

        if dtype == torch.bfloat16:
            min_val = -3.389531389251535e+38
            max_val = 3.389531389251535e+38
        else:
            min_val = torch.finfo(dtype).min
            max_val = torch.finfo(dtype).max

        values = [double_min, float_min, -42, 0, 42, float_max, double_max]

        for from_ in values:
            for to_ in values:
                t = torch.empty(size, dtype=dtype, device=device)
                if not (min_val <= from_ <= max_val) or not (min_val <= to_ <= max_val):
                    pass
                elif to_ < from_:
                    self.assertRaisesRegex(
                        RuntimeError,
                        "uniform_ expects to return",
                        lambda: t.uniform_(from_, to_)
                    )
                elif to_ - from_ > max_val:
                    self.assertRaisesRegex(
                        RuntimeError,
                        "uniform_ expects to-from",
                        lambda: t.uniform_(from_, to_)
                    )
                else:
                    t.uniform_(from_, to_)
                    range_ = to_ - from_
                    if dtype != torch.bfloat16 and not (
                            dtype == torch.half and device == 'cpu') and not torch.isnan(t).all():
                        delta = alpha * range_
                        double_t = t.to(torch.double)
                        if range_ == 0:
                            self.assertTrue(double_t.min() == from_)
                            self.assertTrue(double_t.max() == to_)
                        elif dtype == torch.half:
                            self.assertTrue(from_ <= double_t.min() <= (from_ + delta))
                            self.assertTrue((to_ - delta) <= double_t.max() <= to_)
                        else:
                            self.assertTrue(from_ <= double_t.min() <= (from_ + delta))
                            self.assertTrue((to_ - delta) <= double_t.max() < to_)