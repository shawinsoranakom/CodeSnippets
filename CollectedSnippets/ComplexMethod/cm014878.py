def test_random_from_to(self, device, dtype):
        size = 2000
        alpha = 0.1

        int64_min_val = torch.iinfo(torch.int64).min
        int64_max_val = torch.iinfo(torch.int64).max

        if dtype in [torch.float, torch.double, torch.half]:
            min_val = int(max(torch.finfo(dtype).min, int64_min_val))
            max_val = int(min(torch.finfo(dtype).max, int64_max_val))
            froms = [min_val, -42, 0, 42]
            tos = [-42, 0, 42, max_val >> 1]
        elif dtype == torch.bfloat16:
            min_val = int64_min_val
            max_val = int64_max_val
            froms = [min_val, -42, 0, 42]
            tos = [-42, 0, 42, max_val >> 1]
        elif dtype == torch.uint8:
            min_val = torch.iinfo(dtype).min
            max_val = torch.iinfo(dtype).max
            froms = [int64_min_val, -42, min_val - 1, min_val, 42, max_val, max_val + 1]
            tos = [-42, min_val - 1, min_val, 42, max_val, max_val + 1, int64_max_val]
        elif dtype == torch.int64:
            min_val = int64_min_val
            max_val = int64_max_val
            froms = [min_val, -42, 0, 42]
            tos = [-42, 0, 42, max_val]
        else:
            min_val = torch.iinfo(dtype).min
            max_val = torch.iinfo(dtype).max
            froms = [int64_min_val, min_val - 1, min_val, -42, 0, 42, max_val, max_val + 1]
            tos = [min_val - 1, min_val, -42, 0, 42, max_val, max_val + 1, int64_max_val]

        if dtype == torch.double:
            fp_limit = 2**53
        elif dtype == torch.float:
            fp_limit = 2**24
        elif dtype == torch.half:
            fp_limit = 2**11
        elif dtype == torch.bfloat16:
            fp_limit = 2**8
        else:
            fp_limit = 0

        for from_ in froms:
            for to_ in tos:
                t = torch.empty(size, dtype=dtype, device=device)
                if to_ > from_:
                    if not (min_val <= from_ <= max_val):
                        self.assertRaisesRegex(
                            RuntimeError,
                            "from is out of bounds",
                            lambda: t.random_(from_, to_)
                        )
                    elif not (min_val <= (to_ - 1) <= max_val):
                        self.assertRaisesRegex(
                            RuntimeError,
                            "to - 1 is out of bounds",
                            lambda: t.random_(from_, to_)
                        )
                    else:
                        if dtype.is_floating_point and (
                                not (-fp_limit <= from_ <= fp_limit) or not (-fp_limit <= (to_ - 1) <= fp_limit)):
                            if not (-fp_limit <= from_ <= fp_limit):
                                self.assertWarnsRegex(UserWarning, "from is out of bounds",
                                                      lambda: t.random_(from_, to_))
                            if not (-fp_limit <= (to_ - 1) <= fp_limit):
                                self.assertWarnsRegex(UserWarning, "to - 1 is out of bounds",
                                                      lambda: t.random_(from_, to_))
                        else:
                            t.random_(from_, to_)
                            range_ = to_ - from_
                            delta = max(1, alpha * range_)
                            if dtype == torch.bfloat16:
                                # Less strict checks because of rounding errors
                                # TODO investigate rounding errors
                                self.assertTrue(from_ <= t.to(torch.double).min() < (from_ + delta))
                                self.assertTrue((to_ - delta) < t.to(torch.double).max() <= to_)
                            else:
                                self.assertTrue(from_ <= t.to(torch.double).min() < (from_ + delta))
                                self.assertTrue((to_ - delta) <= t.to(torch.double).max() < to_)
                else:
                    self.assertRaisesRegex(
                        RuntimeError,
                        "random_ expects 'from' to be less than 'to', but got from=" + str(from_) + " >= to=" + str(to_),
                        lambda: t.random_(from_, to_)
                    )