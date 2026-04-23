def test_builtin_map(self):
        self.assertEqual(list(map(lambda x: x+1, SequenceClass(5))),
                         list(range(1, 6)))

        d = {"one": 1, "two": 2, "three": 3}
        self.assertEqual(list(map(lambda k, d=d: (k, d[k]), d)),
                         list(d.items()))
        dkeys = list(d.keys())
        expected = [(i < len(d) and dkeys[i] or None,
                     i,
                     i < len(d) and dkeys[i] or None)
                    for i in range(3)]

        f = open(TESTFN, "w", encoding="utf-8")
        try:
            for i in range(10):
                f.write("xy" * i + "\n") # line i has len 2*i+1
        finally:
            f.close()
        f = open(TESTFN, "r", encoding="utf-8")
        try:
            self.assertEqual(list(map(len, f)), list(range(1, 21, 2)))
        finally:
            f.close()
            try:
                unlink(TESTFN)
            except OSError:
                pass