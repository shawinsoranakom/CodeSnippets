def test_optionalSlicing(self):
        for func, data, elem, expected in self.precomputedCases:
            for lo in range(4):
                lo = min(len(data), lo)
                for hi in range(3,8):
                    hi = min(len(data), hi)
                    ip = func(data, elem, lo, hi)
                    self.assertTrue(lo <= ip <= hi)
                    if func is self.module.bisect_left and ip < hi:
                        self.assertTrue(elem <= data[ip])
                    if func is self.module.bisect_left and ip > lo:
                        self.assertTrue(data[ip-1] < elem)
                    if func is self.module.bisect_right and ip < hi:
                        self.assertTrue(elem < data[ip])
                    if func is self.module.bisect_right and ip > lo:
                        self.assertTrue(data[ip-1] <= elem)
                    self.assertEqual(ip, max(lo, min(hi, expected)))