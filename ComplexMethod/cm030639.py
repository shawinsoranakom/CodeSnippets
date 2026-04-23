def test_basic(self):
        # Check that comparisons involving Number objects
        # give the same results give as comparing the
        # corresponding ints
        for a in range(3):
            for b in range(3):
                for typea in (int, Number):
                    for typeb in (int, Number):
                        if typea==typeb==int:
                            continue # the combination int, int is useless
                        ta = typea(a)
                        tb = typeb(b)
                        for ops in opmap.values():
                            for op in ops:
                                realoutcome = op(a, b)
                                testoutcome = op(ta, tb)
                                self.assertEqual(realoutcome, testoutcome)