def test_popitem(self):
        # dict.popitem()
        for copymode in -1, +1:
            # -1: b has same structure as a
            # +1: b is a.copy()
            for log2size in range(4):
                size = 2**log2size
                a = {}
                b = {}
                for i in range(size):
                    a[repr(i)] = i
                    if copymode < 0:
                        b[repr(i)] = i
                if copymode > 0:
                    b = a.copy()
                for i in range(size):
                    ka, va = ta = a.popitem()
                    self.assertEqual(va, int(ka))
                    kb, vb = tb = b.popitem()
                    self.assertEqual(vb, int(kb))
                    self.assertFalse(copymode < 0 and ta != tb)
                self.assertFalse(a)
                self.assertFalse(b)

        d = {}
        self.assertRaises(KeyError, d.popitem)